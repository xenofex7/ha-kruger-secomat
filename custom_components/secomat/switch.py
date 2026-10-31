from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SecomatAPIError
from .const import DOMAIN
from .coordinator import SecomatCoordinator
from .entity import SecomatEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.unique_id

    entities = [
        SecomatLaundryDryingSwitch(coordinator, serial),
        SecomatRoomDryingSwitch(coordinator, serial),
        SecomatMoistureLockSwitch(coordinator, serial),
    ]

    async_add_entities(entities)


class SecomatLaundryDryingSwitch(SecomatEntity, SwitchEntity):
    _attr_name = "Laundry Drying"
    _attr_icon = "mdi:washing-machine"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _key = "laundry_drying"

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data.get("secomat_state", 0)
        mode = self.coordinator.data.get("operating_mode", 0)
        return state > 0 and mode == 2

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self.coordinator.api.start_laundry_drying()
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to turn on laundry drying: {err}") from err

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self.coordinator.api.turn_off()
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to turn off Secomat: {err}") from err


class SecomatRoomDryingSwitch(SecomatEntity, SwitchEntity):
    _attr_name = "Room Drying"
    _attr_icon = "mdi:home-thermometer"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _key = "room_drying"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("room_drying_enabled", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self.coordinator.api.start_room_drying()
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to turn on room drying: {err}") from err

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self.coordinator.api.stop_room_drying()
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to turn off room drying: {err}") from err


class SecomatMoistureLockSwitch(SecomatEntity, SwitchEntity):
    _attr_name = "Moisture Lock"
    _attr_icon = "mdi:lock"
    _attr_entity_category = EntityCategory.CONFIG
    _key = "moisture_lock"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("target_humidity_level_locked", 0))

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self.coordinator.api.set_moisture_lock(True)
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to lock moisture: {err}") from err

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self.coordinator.api.set_moisture_lock(False)
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to unlock moisture: {err}") from err
