"""Select platform for Krüger Secomat.

Target moisture select entity discovered by @ratsch (https://github.com/ratsch/ha-kruger-secomat).
Command: PARAMETER_CHANGE with args {"residual_moisture_target": 0-3}
"""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SecomatAPIError
from .const import DOMAIN, HUMIDITY_LEVELS
from .coordinator import SecomatCoordinator

_LOGGER = logging.getLogger(__name__)

MOISTURE_OPTIONS = ["very_dry", "dry", "medium", "moist"]
MOISTURE_LEVEL_MAP = {v: k for k, v in HUMIDITY_LEVELS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat select entities."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")
    async_add_entities([SecomatTargetMoistureSelect(coordinator, entry, serial)])


class SecomatTargetMoistureSelect(CoordinatorEntity[SecomatCoordinator], SelectEntity):
    """Select entity for target moisture level."""

    _attr_has_entity_name = True
    _attr_name = "Target Moisture"
    _attr_icon = "mdi:water-percent"
    _attr_options = MOISTURE_OPTIONS

    def __init__(self, coordinator: SecomatCoordinator, entry: ConfigEntry, serial: str) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"{serial}_target_moisture"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"Secomat {serial}",
            "manufacturer": "Krüger",
            "model": "Secomat",
        }

    @property
    def current_option(self) -> str | None:
        level = self.coordinator.data.get("target_humidity_level")
        return HUMIDITY_LEVELS.get(level)

    async def async_select_option(self, option: str) -> None:
        level = MOISTURE_LEVEL_MAP.get(option)
        if level is None:
            return
        try:
            await self.coordinator.api.set_target_moisture(level)
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            _LOGGER.error("Failed to set target moisture: %s", err)
