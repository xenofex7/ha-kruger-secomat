"""Select platform for Krüger Secomat."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SecoматAPIError
from .const import DOMAIN, HUMIDITY_LEVELS
from .coordinator import SecomatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat select entities."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")

    async_add_entities([SecomatTargetHumiditySelect(coordinator, entry, serial)])


class SecomatTargetHumiditySelect(CoordinatorEntity[SecomatCoordinator], SelectEntity):
    """Secomat target humidity level select."""

    _attr_has_entity_name = True
    _attr_name = "Target Moisture"
    _attr_icon = "mdi:water-percent"
    _attr_options = ["wet", "dry", "extra_dry"]

    def __init__(
        self,
        coordinator: SecomatCoordinator,
        entry: ConfigEntry,
        serial: str,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"{serial}_target_humidity"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"Secomat {serial}",
            "manufacturer": "Krüger",
            "model": "Secomat",
        }

    @property
    def current_option(self) -> str | None:
        """Return the current target humidity level."""
        level = self.coordinator.data.get("target_humidity_level", 1)
        return HUMIDITY_LEVELS.get(level, "dry")

    async def async_select_option(self, option: str) -> None:
        """Set the target humidity level."""
        level_map = {v: k for k, v in HUMIDITY_LEVELS.items()}
        level = level_map.get(option)
        if level is not None:
            try:
                await self.coordinator.api.send_command(
                    "SET_TARGET_HUMIDITY", {"level": level}
                )
                await self.coordinator.async_request_refresh()
            except SecoматAPIError as err:
                _LOGGER.error("Failed to set target humidity: %s", err)
