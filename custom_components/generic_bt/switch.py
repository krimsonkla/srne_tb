"""Support for SRNE Inverter switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, REG_CMD_POWER_ON_OFF, REG_DC_LOAD_SWITCH
from .coordinator import GenericBTCoordinator
from .entity import GenericBTEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the SRNE Inverter switches."""
    coordinator: GenericBTCoordinator = hass.data[DOMAIN][entry.entry_id]

    switches = [
        SRNESwitch(coordinator, "inverter_power", "Inverter Power", REG_CMD_POWER_ON_OFF),
        SRNESwitch(coordinator, "dc_load", "DC Load", REG_DC_LOAD_SWITCH),
    ]

    async_add_entities(switches)

class SRNESwitch(GenericBTEntity, SwitchEntity):
    """Representation of an SRNE Inverter switch."""

    def __init__(
        self,
        coordinator: GenericBTCoordinator,
        key: str,
        name: str,
        register: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._register = register
        self._attr_unique_id = f"{coordinator.base_unique_id}_{key}"

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        # For inverter power (0xDF00): 1 is ON, 0 is OFF
        # For DC load (0xE216): 1 is ON, 0 is OFF
        # We need to make sure these are polled or updated
        val = self._device.data.get(self._key)
        if val is None:
            return None
        return val == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._device.write_register(self._register, 1)
        self._device.data[self._key] = 1
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._device.write_register(self._register, 0)
        self._device.data[self._key] = 0
        self.async_write_ha_state()
