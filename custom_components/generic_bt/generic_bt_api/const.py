"""Constants for SRNE Energy Storage Inverter."""

# GATT UUIDs (These should be replaced with actual UUIDs if known,
# but for now we keep the GATT proxy functionality)
# Based on common Bluetooth to RS485 bridges, there might be specific UUIDs.
# Since modbus.md doesn't specify UUIDs, we assume they are provided via config or discovered.

# Default Slave ID
DEFAULT_SLAVE_ID = 1

# Register addresses from modbus.md
# P01: DC Data Area
REG_BAT_SOC = 0x0100  # %
REG_BAT_VOLT = 0x0101  # 0.1 V
REG_BAT_CURR = 0x0102  # 0.1 A
REG_BAT_TEMP = 0x0103  # 0.1 °C
REG_PV1_VOLT = 0x0107  # 0.1 V
REG_PV1_CURR = 0x0108  # 0.1 A
REG_PV1_POWER = 0x0109  # 1 W
REG_PV_TOTAL_POWER = 0x010A  # 1 W
REG_CHARGE_STATE = 0x010B
REG_CHARGE_POWER = 0x010E  # 1 W

# P02: Inverter Data Area
REG_MACHINE_STATE = 0x0210
REG_BUS_VOLT = 0x0212  # 0.1 V
REG_GRID_VOLT = 0x0213  # 0.1 V
REG_GRID_CURR = 0x0214  # 0.1 A
REG_GRID_FREQ = 0x0215  # 0.01 Hz
REG_INV_VOLT = 0x0216  # 0.1 V
REG_INV_CURR = 0x0217  # 0.1 A
REG_INV_FREQ = 0x0218  # 0.01 Hz
REG_LOAD_CURR = 0x0219  # 0.1 A
REG_LOAD_ACTIVE_POWER = 0x021B  # 1 W
REG_LOAD_APPARENT_POWER = 0x021C  # 1 VA
REG_LOAD_RATIO = 0x021F  # 1 %
REG_TEMP_DC_DC = 0x0220  # 0.1 °C
REG_TEMP_DC_AC = 0x0221  # 0.1 °C

# P03: Device Control Area
REG_CMD_POWER_ON_OFF = 0xDF00

# P07: Inverter Settings
REG_DC_LOAD_SWITCH = 0xE216

