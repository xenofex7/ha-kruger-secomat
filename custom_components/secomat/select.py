"""Select platform for Krüger Secomat.

Target moisture select entity discovered by @ratsch (https://github.com/ratsch/ha-kruger-secomat).
Command: PARAMETER_CHANGE with args {"residual_moisture_target": 0-3}
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SecomatAPIError
from .const import DOMAIN, HUMIDITY_LEVELS
from .coordinator import SecomatCoordinator
from .entity import SecomatEntity

MOISTURE_LEVEL_MAP = {v: k for k, v in HUMIDITY_LEVELS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat select entities."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.unique_id
    async_add_entities([SecomatTargetMoistureSelect(coordinator, serial)])


class SecomatTargetMoistureSelect(SecomatEntity, SelectEntity):
    """Select entity for target moisture level."""

    _attr_name = "Target Moisture"
    _attr_icon = "mdi:water-percent"
    _attr_options = list(HUMIDITY_LEVELS.values())
    _key = "target_moisture"

    @property
    def current_option(self) -> str | None:
        level = self.coordinator.data.get("target_humidity_level")
        return HUMIDITY_LEVELS.get(level)

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.api.set_target_moisture(MOISTURE_LEVEL_MAP[option])
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to set target moisture: {err}") from err
