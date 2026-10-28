"""Binary sensor platform for Krüger Secomat."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SecomatCoordinator
from .entity import SecomatEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat binary sensors."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.unique_id

    async_add_entities(
        [
            SecomatEyeBinarySensor(coordinator, serial),
            SecomatBacklightBinarySensor(coordinator, serial),
            SecomatProblemBinarySensor(coordinator, serial),
        ]
    )


class SecomatEyeBinarySensor(SecomatEntity, BinarySensorEntity):
    """Detects whether the device's eye sensor sees an object."""

    _attr_name = "Eye Detects Object"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:eye"
    _key = "eye_seeing_object"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get("eye_seeing_object")
        return bool(val) if val is not None else None


class SecomatBacklightBinarySensor(SecomatEntity, BinarySensorEntity):
    """Reports whether the HMI backlight is on."""

    _attr_name = "Display Backlight"
    _attr_icon = "mdi:monitor-shimmer"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _key = "hmi_backlight"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get("hmi_backlight")
        return bool(val) if val is not None else None


class SecomatProblemBinarySensor(SecomatEntity, BinarySensorEntity):
    """On when the device reports one or more errors."""

    _attr_name = "Problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _key = "problem"

    @property
    def is_on(self) -> bool:
        errors = self.coordinator.data.get("error_list") or []
        return len(errors) > 0

    @property
    def extra_state_attributes(self) -> dict:
        return {"errors": self.coordinator.data.get("error_list") or []}
