from uuid import UUID
import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient
from bleak.exc import BleakError

from .modbus_codec import build_read_request, build_write_request, parse_response
from .const import DEFAULT_SLAVE_ID, REG_BAT_SOC, REG_BAT_VOLT, REG_MACHINE_STATE

_LOGGER = logging.getLogger(__name__)

class GenericBTDevice:
    """Generic BT Device Class implementing Modbus-over-Bluetooth."""
    def __init__(self, ble_device):
        self._ble_device = ble_device
        self._client: BleakClient | None = None
        self._client_stack = AsyncExitStack()
        self._lock = asyncio.Lock()
        self._slave_id = DEFAULT_SLAVE_ID
        self._write_uuid = None
        self._read_uuid = None
        self.data = {}

    def set_uuids(self, write_uuid, read_uuid):
        """Set the GATT UUIDs for Modbus communication."""
        self._write_uuid = write_uuid
        self._read_uuid = read_uuid

    async def update(self):
        """Update device data by polling Modbus registers."""
        try:
            # Poll P01 DC Data Area (0x0100 - 0x0111)
            p01_data = await self.read_registers(0x0100, 18)
            if p01_data:
                self._parse_p01(p01_data)

            # Poll P02 Inverter Data Area (0x0210 - 0x0223)
            p02_data = await self.read_registers(0x0210, 20)
            if p02_data:
                self._parse_p02(p02_data)
        except Exception as exc:
            _LOGGER.error(f"Error updating device data: {exc}")

    def _parse_p01(self, registers):
        """Parse P01 registers."""
        if len(registers) < 18:
            return
        self.data["bat_soc"] = registers[0x0100 - 0x0100]
        self.data["bat_volt"] = registers[0x0101 - 0x0100] * 0.1
        # Battery current is signed
        curr = registers[0x0102 - 0x0100]
        if curr > 0x7FFF:
            curr -= 0x10000
        self.data["bat_curr"] = curr * 0.1
        self.data["bat_temp"] = registers[0x0103 - 0x0100] * 0.1
        self.data["pv1_volt"] = registers[0x0107 - 0x0100] * 0.1
        self.data["pv1_curr"] = registers[0x0108 - 0x0100] * 0.1
        self.data["pv1_power"] = registers[0x0109 - 0x0100]
        self.data["pv_total_power"] = registers[0x010A - 0x0100]
        self.data["charge_state"] = registers[0x010B - 0x0100]
        self.data["charge_power"] = registers[0x010E - 0x0100]

    def _parse_p02(self, registers):
        """Parse P02 registers."""
        if len(registers) < 20:
            return
        self.data["machine_state"] = registers[0x0210 - 0x0210]
        self.data["bus_volt"] = registers[0x0212 - 0x0210] * 0.1
        self.data["grid_volt"] = registers[0x0213 - 0x0210] * 0.1
        self.data["grid_curr"] = registers[0x0214 - 0x0210] * 0.1
        self.data["grid_freq"] = registers[0x0215 - 0x0210] * 0.01
        self.data["inv_volt"] = registers[0x0216 - 0x0210] * 0.1
        self.data["inv_curr"] = registers[0x0217 - 0x0210] * 0.1
        self.data["inv_freq"] = registers[0x0218 - 0x0210] * 0.01
        self.data["load_curr"] = registers[0x0219 - 0x0210] * 0.1
        self.data["load_active_power"] = registers[0x021B - 0x0210]
        self.data["load_apparent_power"] = registers[0x021C - 0x0210]
        self.data["load_ratio"] = registers[0x021F - 0x0210]
        self.data["temp_dc_dc"] = registers[0x0220 - 0x0210] * 0.1
        self.data["temp_dc_ac"] = registers[0x0221 - 0x0210] * 0.1

    async def stop(self):
        async with self._lock:
            if self._client:
                await self._client_stack.aclose()
                self._client = None

    @property
    def connected(self):
        return self._client is not None and self._client.is_connected

    async def get_client(self):
        async with self._lock:
            if not self._client or not self._client.is_connected:
                _LOGGER.debug("Connecting to %s", self._ble_device.address)
                try:
                    self._client = await self._client_stack.enter_async_context(BleakClient(self._ble_device, timeout=30.0))
                except Exception as exc:
                    _LOGGER.error("Failed to connect to %s: %s", self._ble_device.address, exc)
                    self._client = None
                    raise

    async def read_registers(self, address, count):
        """Read multiple registers using Modbus-RTU over Bluetooth."""
        request = build_read_request(self._slave_id, address, count)
        response = await self._send_modbus_request(request)
        if response:
            return parse_response(response, self._slave_id, 0x03)
        return None

    async def write_register(self, address, value):
        """Write a single register using Modbus-RTU over Bluetooth."""
        request = build_write_request(self._slave_id, address, value)
        response = await self._send_modbus_request(request)
        if response:
            return parse_response(response, self._slave_id, 0x06)
        return None

    async def _send_modbus_request(self, request):
        """Send a Modbus request and wait for response."""
        await self.get_client()
        if not self._write_uuid or not self._read_uuid:
            # If UUIDs are not set, we can't communicate.
            # In a real integration, we should discover them or have defaults.
            # For now, let's assume they are set or try to find them.
            if not await self._discover_uuids():
                _LOGGER.error("GATT UUIDs for Modbus not set and could not be discovered")
                return None

        # Some devices use the same UUID for write and notify
        # We'll use a Future to wait for the notification response
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def notification_handler(sender, data):
            if not future.done():
                future.set_result(data)

        await self._client.start_notify(self._read_uuid, notification_handler)
        try:
            await self._client.write_gatt_char(self._write_uuid, request, response=True)
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=5.0)
            return response
        finally:
            await self._client.stop_notify(self._read_uuid)

    async def _discover_uuids(self):
        """Attempt to discover appropriate UUIDs for Modbus communication."""
        # This is a heuristic. Many BT-RS485 bridges use specific characteristics.
        # For now, we'll just look for characteristics that support write and notify.
        for service in self._client.services:
            for char in service.characteristics:
                if "write" in char.properties and ("notify" in char.properties or "indicate" in char.properties):
                    self._write_uuid = char.uuid
                    self._read_uuid = char.uuid
                    _LOGGER.info(f"Discovered Modbus UUID: {char.uuid}")
                    return True
        return False

    async def write_gatt(self, target_uuid, data):
        """Raw GATT write (legacy support)."""
        await self.get_client()
        data_as_bytes = bytearray.fromhex(data)
        await self._client.write_gatt_char(target_uuid, data_as_bytes, True)

    async def read_gatt(self, target_uuid):
        """Raw GATT read (legacy support)."""
        await self.get_client()
        return await self._client.read_gatt_char(target_uuid)

    def update_from_advertisement(self, advertisement):
        """Update state from advertisement data if available."""
        pass
