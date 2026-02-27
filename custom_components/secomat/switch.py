"""Switch platform for Krüger Secomat."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SecoматAPIError
from .const import DOMAIN
from .coordinator import SecomatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat switches."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")

    entities = [
        SecomatPowerSwitch(coordinator, entry, serial),
        SecomatRoomDryingSwitch(coordinator, entry, serial),
    ]

    async_add_entities(entities)


class SecomatBaseSwitch(CoordinatorEntity[SecomatCoordinator], SwitchEntity):
    """Base class for Secomat switches."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SecomatCoordinator,
        entry: ConfigEntry,
        serial: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"Secomat {serial}",
            "manufacturer": "Krüger",
            "model": "Secomat",
        }


class SecomatPowerSwitch(SecomatBaseSwitch):
    """Secomat power switch (laundry drying)."""

    _attr_name = "Laundry Drying"
    _attr_icon = "mdi:washing-machine"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_laundry_drying"

    @property
    def is_on(self) -> bool:
        """Return true if laundry drying is active."""
        state = self.coordinator.data.get("secomat_state", 0)
        mode = self.coordinator.data.get("operating_mode", 0)
        return state > 0 and mode in (1, 2)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on laundry drying."""
        try:
            await self.coordinator.api.start_laundry_drying()
            await self.coordinator.async_request_refresh()
        except SecoматAPIError as err:
            _LOGGER.error("Failed to turn on laundry drying: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the Secomat."""
        try:
            await self.coordinator.api.turn_off()
            await self.coordinator.async_request_refresh()
        except SecoматAPIError as err:
            _LOGGER.error("Failed to turn off Secomat: %s", err)


class SecomatRoomDryingSwitch(SecomatBaseSwitch):
    """Secomat room drying switch."""

    _attr_name = "Room Drying"
    _attr_icon = "mdi:home-thermometer"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_room_drying"

    @property
    def is_on(self) -> bool:
        """Return true if room drying is enabled."""
        return self.coordinator.data.get("room_drying_enabled", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on room drying."""
        try:
            await self.coordinator.api.start_room_drying()
            await self.coordinator.async_request_refresh()
        except SecoматAPIError as err:
            _LOGGER.error("Failed to turn on room drying: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off room drying."""
        try:
            await self.coordinator.api.stop_room_drying()
            await self.coordinator.async_request_refresh()
        except SecoматAPIError as err:
            _LOGGER.error("Failed to turn off room drying: %s", err)
