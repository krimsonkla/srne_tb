"""Support for SRNE Inverter sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GenericBTCoordinator
from .entity import GenericBTEntity

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the SRNE Inverter sensors."""
    coordinator: GenericBTCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        SRNESensor(coordinator, "bat_soc", "Battery SOC", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "bat_volt", "Battery Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "bat_curr", "Battery Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "bat_temp", "Battery Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "pv1_volt", "PV1 Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "pv1_curr", "PV1 Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "pv1_power", "PV1 Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "pv_total_power", "PV Total Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "charge_power", "Charge Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "grid_volt", "Grid Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "grid_curr", "Grid Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "grid_freq", "Grid Frequency", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "inv_volt", "Inverter Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "inv_curr", "Inverter Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "inv_freq", "Inverter Frequency", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "load_active_power", "Load Active Power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "load_ratio", "Load Ratio", PERCENTAGE, None, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "temp_dc_dc", "DC-DC Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        SRNESensor(coordinator, "temp_dc_ac", "DC-AC Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    ]

    async_add_entities(sensors)

class SRNESensor(GenericBTEntity, SensorEntity):
    """Representation of an SRNE Inverter sensor."""

    def __init__(
        self,
        coordinator: GenericBTCoordinator,
        key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{coordinator.base_unique_id}_{key}"

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        return self._device.data.get(self._key)
