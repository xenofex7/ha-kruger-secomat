from __future__ import annotations

import voluptuous as vol
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SecomatAPIError
from .const import DOMAIN, SERVICE_START_DRYING
from .coordinator import SecomatCoordinator
from .entity import SecomatEntity

_MAX_DELAY_SECONDS = 24 * 60 * 60


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.unique_id

    async_add_entities([SecomatManualButton(coordinator, serial)])

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


class SecomatManualButton(SecomatEntity, ButtonEntity):
    _attr_name = "Start Manual Drying"
    _attr_icon = "mdi:washing-machine-alert"
    _key = "start_manual"

    async def async_press(self) -> None:
        await self.async_start_drying(delay_seconds=0)

    async def async_start_drying(self, delay_seconds: int = 0) -> None:
        try:
            await self.coordinator.api.start_laundry_drying_manual(delay_seconds)
            await self.coordinator.async_request_refresh()
        except SecomatAPIError as err:
            raise HomeAssistantError(f"Failed to start manual drying: {err}") from err
