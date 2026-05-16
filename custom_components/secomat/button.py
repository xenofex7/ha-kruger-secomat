"""Button platform for Krüger Secomat."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SecomatAPIError
from .const import DOMAIN, SERVICE_START_DRYING
from .coordinator import SecomatCoordinator

_LOGGER = logging.getLogger(__name__)

# Upper bound = 24h. The device accepts larger values, but a one-day window
# is the sane practical limit and protects against typos like 360000.
_MAX_DELAY_SECONDS = 24 * 60 * 60


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat buttons."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")

    async_add_entities([SecomatManualButton(coordinator, entry, serial)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_START_DRYING,
        {
            vol.Optional("delay_seconds", default=0): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=_MAX_DELAY_SECONDS)
            ),
        },
        "async_start_drying",
    )


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
        await self.async_start_drying(delay_seconds=0)

    async def async_start_drying(self, delay_seconds: int = 0) -> None:
        """Start manual drying, optionally after delay_seconds."""
        try:
            await self.coordinator.api.start_laundry_drying_manual(delay_seconds)
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            _LOGGER.error(
                "Failed to start manual drying (delay_seconds=%s): %s",
                delay_seconds,
                err,
            )
