# Generic Bluetooth (SRNE Inverter) for Home Assistant

This Home Assistant integration provides support for SRNE Energy Storage Inverters (and similar controllers) communicating via Bluetooth using the Modbus-RTU protocol over a Bluetooth-to-RS485 bridge.

## Features

- **Real-time Monitoring**: Tracks battery, PV, grid, and inverter metrics.
- **Control**: Toggle Inverter Power and DC Load directly from Home Assistant.
- **Auto-Discovery**: Automatically finds and identifies compatible Bluetooth devices.
- **GATT Proxy Services**: Provides raw `read_gatt` and `write_gatt` services for advanced debugging.

### Supported Entities

#### Sensors
- **Battery**: SOC (%), Voltage (V), Current (A), Temperature (°C)
- **Solar (PV)**: PV1 Voltage, PV1 Current, PV1 Power, Total PV Power
- **Grid**: Voltage, Current, Frequency
- **Inverter**: Output Voltage, Output Current, Output Frequency, Charge Power
- **Load**: Active Power (W), Load Ratio (%)
- **Diagnostics**: DC-DC Temperature, DC-AC Temperature

#### Switches
- **Inverter Power**: Turn the inverter output on or off.
- **DC Load**: Control the DC load output.

#### Binary Sensors
- **Connection Status**: Indicates if the device is currently connected via Bluetooth.
- **Attributes**: Displays `charge_state` and `machine_state` codes.

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Add the URL of this repository and select **Integration** as the category.
5. Click **Add**, then find "Generic Bluetooth Integration" and click **Download**.
6. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the `custom_components/generic_bt` folder from this repository.
2. Copy it into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Setup

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Generic Bluetooth**.
3. The integration will scan for nearby Bluetooth devices. Select your inverter/Bluetooth bridge from the list.
4. Once added, the entities will be created automatically.

## Testing & Verification

### 1. Check Connection
Ensure the `binary_sensor` for your device shows "Connected". If it stays "Disconnected", ensure the Bluetooth bridge is powered and within range of your Home Assistant host.

### 2. Verify Data
Check the sensor values (e.g., Battery Voltage, PV Power) against your inverter's display or official app to ensure the scaling and units are correct.

### 3. Test Controls
Try toggling the **Inverter Power** switch. 
*Note: Use caution when toggling power if you have critical loads connected.*

### 4. Advanced: GATT Services
If you need to send custom Modbus commands or investigate GATT characteristics:
1. Go to **Developer Tools** > **Services**.
2. Search for `generic_bt.write_gatt` or `generic_bt.read_gatt`.
3. Provide the `target_uuid` and `data` (in hex format for writes).

## Technical Details

- **Protocol**: Modbus-RTU over Bluetooth GATT.
- **Polling Interval**: Data is polled every 60 seconds.
- **Bluetooth Requirements**: Requires a Home Assistant host with working Bluetooth (Internal adapter or Bluetooth Proxy).
