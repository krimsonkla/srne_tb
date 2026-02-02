"""Constants for SRNE Energy Storage Inverter."""

# GATT UUIDs (These should be replaced with actual UUIDs if known,
# but for now we keep the GATT proxy functionality)
# Based on common Bluetooth to RS485 bridges, there might be specific UUIDs.
# Since modbus.md doesn't specify UUIDs, we assume they are provided via config or discovered.

# Default Slave ID (255 is used by SolarLink/SRNE devices)
DEFAULT_SLAVE_ID = 255

# Register addresses from modbus.md
# P01: DC Data Area (0x0100 - 0x0111)
REG_BAT_SOC = 0x0100  # % - Battery State of Charge
REG_BAT_VOLT = 0x0101  # 0.1 V - Battery Voltage
REG_BAT_CURR = 0x0102  # 0.1 A - Battery Current (signed: >0 discharge, <0 charge)
REG_BAT_TEMP = 0x0103  # 0.1 °C - Battery Temperature (signed)
REG_PV1_VOLT = 0x0107  # 0.1 V - PV Panel 1 Voltage
REG_PV1_CURR = 0x0108  # 0.1 A - PV Panel 1 Current
REG_PV1_POWER = 0x0109  # 1 W - PV Panel 1 Power
REG_PV_TOTAL_POWER = 0x010A  # 1 W - Total PV Power
REG_CHARGE_STATE = 0x010B  # Charge State (0=off, 1=quick, 2=const volt, 4=float, 6=activate, 8=full)
REG_CHARGE_POWER = 0x010E  # 1 W - Total Charge Power (PV + AC)
REG_PV2_VOLT = 0x010F  # 0.1 V - PV Panel 2 Voltage
REG_PV2_CURR = 0x0110  # 0.1 A - PV Panel 2 Current
REG_PV2_POWER = 0x0111  # 1 W - PV Panel 2 Power

# P02: Inverter Data Area (0x0210 - 0x0243)
REG_MACHINE_STATE = 0x0210  # Machine State (0-10, see modbus.md for meanings)
REG_BUS_VOLT = 0x0212  # 0.1 V - Total Bus Voltage
REG_GRID_VOLT = 0x0213  # 0.1 V - Grid Phase-A Voltage
REG_GRID_CURR = 0x0214  # 0.1 A - Grid Phase-A Current
REG_GRID_FREQ = 0x0215  # 0.01 Hz - Grid Frequency
REG_INV_VOLT = 0x0216  # 0.1 V - Inverter Phase-A Output Voltage
REG_INV_CURR = 0x0217  # 0.1 A - Inverter Phase-A Inductive Current
REG_INV_FREQ = 0x0218  # 0.01 Hz - Inverter Frequency
REG_LOAD_CURR = 0x0219  # 0.1 A - Load Phase-A Current
REG_LOAD_ACTIVE_POWER = 0x021B  # 1 W - Load Phase-A Active Power
REG_LOAD_APPARENT_POWER = 0x021C  # 1 VA - Load Phase-A Apparent Power
REG_LINE_CHG_CURR = 0x021E  # 0.1 A - AC Charging Current (battery side)
REG_LOAD_RATIO = 0x021F  # 1 % - Load Ratio Phase-A
REG_TEMP_DC_DC = 0x0220  # 0.1 °C - Cooling-fin DC-DC Temperature (signed)
REG_TEMP_DC_AC = 0x0221  # 0.1 °C - Cooling-fin DC-AC Temperature (signed)
REG_TEMP_TRANSFORMER = 0x0222  # 0.1 °C - Transformer Temperature (signed)
REG_TEMP_AMBIENT = 0x0223  # 0.1 °C - Ambient Temperature (signed)
REG_PV_CHG_CURR = 0x0224  # 0.1 A - PV Charging Current (battery side)

# P03: Device Control Area
REG_CMD_POWER_ON_OFF = 0xDF00  # 0=Off, 1=On
REG_CMD_RESET = 0xDF01  # 1=Reset
REG_CMD_RESTORE_FACTORY = 0xDF02  # 0xAA=restore, 0xBB=clear stats, 0xCC=clear faults

# P07: Inverter Settings
REG_DC_LOAD_SWITCH = 0xE216  # 0=Off, 1=On

# Charge State Values
CHARGE_STATE_OFF = 0
CHARGE_STATE_QUICK = 1
CHARGE_STATE_CONST_VOLT = 2
CHARGE_STATE_FLOAT = 4
CHARGE_STATE_ACTIVATE = 6
CHARGE_STATE_FULL = 8

# Machine State Values
MACHINE_STATE_POWER_ON_DELAY = 0
MACHINE_STATE_STANDBY = 1
MACHINE_STATE_INIT = 2
MACHINE_STATE_SOFT_START = 3
MACHINE_STATE_AC_POWER = 4
MACHINE_STATE_INVERTER = 5
MACHINE_STATE_INV_TO_AC = 6
MACHINE_STATE_AC_TO_INV = 7
MACHINE_STATE_BATTERY_ACTIVATE = 8
MACHINE_STATE_MANUAL_SHUTDOWN = 9
MACHINE_STATE_FAULT = 10

