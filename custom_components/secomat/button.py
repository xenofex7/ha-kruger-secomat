"""Button platform for Krüger Secomat."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SecomatAPIError
from .const import DOMAIN
from .coordinator import SecomatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat buttons."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")

    async_add_entities([SecomatManualButton(coordinator, entry, serial)])


class SecomatBaseButton(CoordinatorEntity[SecomatCoordinator], ButtonEntity):
    """Base class for Secomat buttons."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SecomatCoordinator, entry: ConfigEntry, serial: str) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"Secomat {serial}",
            "manufacturer": "Krüger",
            "model": "Secomat",
            "sw_version": coordinator.data.get("fw_version"),
        }


class SecomatManualButton(SecomatBaseButton):
    """Start laundry drying immediately (manual mode)."""

    _attr_name = "Start Manual Drying"
    _attr_icon = "mdi:washing-machine-alert"

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_start_manual"

    async def async_press(self) -> None:
        try:
            await self.coordinator.api.start_laundry_drying_manual()
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            _LOGGER.error("Failed to start manual drying: %s", err)
