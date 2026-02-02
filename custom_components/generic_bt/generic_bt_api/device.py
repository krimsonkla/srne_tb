import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection
from bluetooth_data_tools import human_readable_name

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
        self._modbus_lock = asyncio.Lock()
        self._slave_id = DEFAULT_SLAVE_ID
        self._write_uuid = None
        self._read_uuid = None
        self.data = {}
        self._notification_future = None
        self._notification_buffer = bytearray()
        self._expected_len = -1
        self._notifications_active = False

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

            # Poll P02 Inverter Data Area (0x0210 - 0x0224)
            p02_data = await self.read_registers(0x0210, 21)
            if p02_data:
                self._parse_p02(p02_data)
        except Exception as exc:
            _LOGGER.error(f"Error updating device data: {exc}")

    def _to_signed(self, value):
        """Convert unsigned 16-bit value to signed."""
        if value > 0x7FFF:
            return value - 0x10000
        return value

    def _parse_p01(self, registers):
        """Parse P01 DC Data Area registers (0x0100 - 0x0111)."""
        if len(registers) < 18:
            return
        self.data["bat_soc"] = registers[0x0100 - 0x0100]
        self.data["bat_volt"] = registers[0x0101 - 0x0100] * 0.1
        # Battery current is signed (>0 discharge, <0 charge)
        self.data["bat_curr"] = self._to_signed(registers[0x0102 - 0x0100]) * 0.1
        # Battery temperature is signed
        self.data["bat_temp"] = self._to_signed(registers[0x0103 - 0x0100]) * 0.1
        self.data["pv1_volt"] = registers[0x0107 - 0x0100] * 0.1
        self.data["pv1_curr"] = registers[0x0108 - 0x0100] * 0.1
        self.data["pv1_power"] = registers[0x0109 - 0x0100]
        self.data["pv_total_power"] = registers[0x010A - 0x0100]
        self.data["charge_state"] = registers[0x010B - 0x0100]
        self.data["charge_power"] = registers[0x010E - 0x0100]
        # PV2 data
        self.data["pv2_volt"] = registers[0x010F - 0x0100] * 0.1
        self.data["pv2_curr"] = registers[0x0110 - 0x0100] * 0.1
        self.data["pv2_power"] = registers[0x0111 - 0x0100]

    def _parse_p02(self, registers):
        """Parse P02 Inverter Data Area registers (0x0210 - 0x0224)."""
        if len(registers) < 21:
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
        self.data["line_chg_curr"] = registers[0x021E - 0x0210] * 0.1
        self.data["load_ratio"] = registers[0x021F - 0x0210]
        # Temperatures are signed
        self.data["temp_dc_dc"] = self._to_signed(registers[0x0220 - 0x0210]) * 0.1
        self.data["temp_dc_ac"] = self._to_signed(registers[0x0221 - 0x0210]) * 0.1
        self.data["temp_transformer"] = self._to_signed(registers[0x0222 - 0x0210]) * 0.1
        self.data["temp_ambient"] = self._to_signed(registers[0x0223 - 0x0210]) * 0.1
        self.data["pv_chg_curr"] = registers[0x0224 - 0x0210] * 0.1

    async def stop(self):
        async with self._lock:
            self._notifications_active = False
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
                    self._client = await self._client_stack.enter_async_context(
                        await establish_connection(
                            BleakClient,
                            self._ble_device,
                            human_readable_name(
                                None, self._ble_device.name, self._ble_device.address
                            ),
                            disconnected_callback=lambda client: _LOGGER.debug(
                                "Disconnected from %s", self._ble_device.address
                            ),
                        )
                    )
                except Exception as exc:
                    _LOGGER.error(
                        "Failed to connect to %s: %s", self._ble_device.address, exc
                    )
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

    def _notification_handler(self, sender, data):
        """Handle incoming notifications from the device."""
        _LOGGER.debug("Received notification on %s: %s", sender, data.hex())
        self._notification_buffer.extend(data)

        # Determine expected length if we have enough bytes
        if self._expected_len == -1 and len(self._notification_buffer) >= 3:
            fn_code = self._notification_buffer[1]
            if fn_code == 0x03:
                # FC 03: [SlaveID][FC][ByteCount][Data...][CRC_L][CRC_H]
                byte_count = self._notification_buffer[2]
                self._expected_len = byte_count + 5
            elif fn_code == 0x06:
                # FC 06: [SlaveID][FC][Addr_H][Addr_L][Val_H][Val_L][CRC_L][CRC_H]
                self._expected_len = 8
            elif fn_code & 0x80:
                # Error response: [SlaveID][FC|0x80][ErrorCode][CRC_L][CRC_H]
                self._expected_len = 5
            else:
                # Unknown function code, assume minimum
                self._expected_len = 5

        if self._expected_len != -1 and len(self._notification_buffer) >= self._expected_len:
            if self._notification_future and not self._notification_future.done():
                result = bytes(self._notification_buffer[:self._expected_len])
                self._notification_future.set_result(result)

    async def _ensure_notifications_started(self):
        """Ensure notifications are started on the read characteristic."""
        if self._notifications_active:
            return
        if not self._read_uuid:
            return
        try:
            _LOGGER.debug("Starting persistent notifications on %s", self._read_uuid)
            await self._client.start_notify(self._read_uuid, self._notification_handler)
            self._notifications_active = True
        except Exception as exc:
            _LOGGER.error("Failed to start notifications: %s", exc)
            raise

    async def _send_modbus_request(self, request):
        """Send a Modbus request and wait for response."""
        async with self._modbus_lock:
            await self.get_client()
            if not self._write_uuid or not self._read_uuid:
                # If UUIDs are not set, we can't communicate.
                # In a real integration, we should discover them or have defaults.
                # For now, let's assume they are set or try to find them.
                if not await self._discover_uuids():
                    _LOGGER.error(
                        "GATT UUIDs for Modbus not set and could not be discovered"
                    )
                    return None

            # Ensure notifications are active (persistent, not per-request)
            await self._ensure_notifications_started()

            # Reset buffer state for this request
            loop = asyncio.get_running_loop()
            self._notification_future = loop.create_future()
            self._notification_buffer = bytearray()
            self._expected_len = -1

            try:
                _LOGGER.debug("Writing request to %s: %s", self._write_uuid, request.hex())
                await self._client.write_gatt_char(self._write_uuid, request, response=False)
                # Wait for response with timeout
                response = await asyncio.wait_for(self._notification_future, timeout=5.0)
                _LOGGER.debug("Received Modbus response: %s", response.hex())
                return response
            except asyncio.TimeoutError:
                _LOGGER.error(
                    "Timeout waiting for Modbus response. Sent: %s, Buffer: %s",
                    request.hex(),
                    self._notification_buffer.hex(),
                )
                return None
            except Exception as exc:
                _LOGGER.exception("Error during Modbus communication: %s", exc)
                return None
            finally:
                self._notification_future = None

    async def _discover_uuids(self):
        """Attempt to discover appropriate UUIDs for Modbus communication."""
        # Well-known UUIDs for SRNE/SolarLink devices (from SolarLink plugin)
        # and additional device UUIDs
        KNOWN_NOTIFY_UUIDS = [
            "0000fff1-0000-1000-8000-00805f9b34fb",  # SolarLink notify
            "53300002-0023-4bd4-bbd5-a6920e4c5653",  # Notify
            "53300003-0023-4bd4-bbd5-a6920e4c5653",  # Indicate
            "53300004-0023-4bd4-bbd5-a6920e4c5653",  # Notify
            "53300005-0023-4bd4-bbd5-a6920e4c5653",  # Notify
        ]
        KNOWN_WRITE_UUIDS = [
            "0000ffd1-0000-1000-8000-00805f9b34fb",  # SolarLink write
            "53300001-0023-4bd4-bbd5-a6920e4c5653",  # Read/Write
        ]

        # Collect all available characteristics
        all_chars = {}
        for service in self._client.services:
            for char in service.characteristics:
                all_chars[char.uuid.lower()] = char
                _LOGGER.debug(
                    "Found characteristic %s with properties: %s",
                    char.uuid,
                    char.properties,
                )

        # Strategy 1: Try well-known UUIDs first
        for notify_uuid in KNOWN_NOTIFY_UUIDS:
            if notify_uuid.lower() in all_chars:
                char = all_chars[notify_uuid.lower()]
                if "notify" in char.properties or "indicate" in char.properties:
                    self._read_uuid = notify_uuid
                    _LOGGER.info("Found known notify UUID: %s", notify_uuid)
                    break

        for write_uuid in KNOWN_WRITE_UUIDS:
            if write_uuid.lower() in all_chars:
                char = all_chars[write_uuid.lower()]
                if "write" in char.properties or "write-without-response" in char.properties:
                    self._write_uuid = write_uuid
                    _LOGGER.info("Found known write UUID: %s", write_uuid)
                    break

        if self._read_uuid and self._write_uuid:
            return True

        # Strategy 2: Look for a single characteristic with both write and notify
        for char in all_chars.values():
            if ("write" in char.properties or "write-without-response" in char.properties) and (
                "notify" in char.properties or "indicate" in char.properties
            ):
                self._write_uuid = char.uuid
                self._read_uuid = char.uuid
                _LOGGER.info("Discovered combined Modbus UUID: %s", char.uuid)
                return True

        # Strategy 3: Find separate write and notify characteristics
        write_char = None
        notify_char = None

        for char in all_chars.values():
            if not write_char and ("write" in char.properties or "write-without-response" in char.properties):
                write_char = char
            if not notify_char and ("notify" in char.properties or "indicate" in char.properties):
                notify_char = char

        if write_char and notify_char:
            self._write_uuid = write_char.uuid
            self._read_uuid = notify_char.uuid
            _LOGGER.info(
                "Discovered separate UUIDs - Write: %s, Notify: %s",
                self._write_uuid,
                self._read_uuid,
            )
            return True

        _LOGGER.warning(
            "Could not discover Modbus UUIDs. Found chars: %s",
            list(all_chars.keys()),
        )
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
