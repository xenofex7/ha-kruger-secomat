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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SecomatCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat binary sensors."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")

    async_add_entities(
        [
            SecomatEyeBinarySensor(coordinator, entry, serial),
            SecomatBacklightBinarySensor(coordinator, entry, serial),
            SecomatProblemBinarySensor(coordinator, entry, serial),
        ]
    )


class SecomatBaseBinarySensor(CoordinatorEntity[SecomatCoordinator], BinarySensorEntity):
    """Base class for Secomat binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SecomatCoordinator,
        entry: ConfigEntry,
        serial: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"Secomat {serial}",
            "manufacturer": "Krüger",
            "model": "Secomat",
            "sw_version": coordinator.data.get("fw_version"),
        }


class SecomatEyeBinarySensor(SecomatBaseBinarySensor):
    """Detects whether the device's eye sensor sees an object."""

    _attr_name = "Eye Detects Object"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:eye"

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_eye_seeing_object"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get("eye_seeing_object")
        return bool(val) if val is not None else None


class SecomatBacklightBinarySensor(SecomatBaseBinarySensor):
    """Reports whether the HMI backlight is on."""

    _attr_name = "Display Backlight"
    _attr_device_class = BinarySensorDeviceClass.LIGHT
    _attr_icon = "mdi:monitor-shimmer"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_hmi_backlight"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get("hmi_backlight")
        return bool(val) if val is not None else None


class SecomatProblemBinarySensor(SecomatBaseBinarySensor):
    """On when the device reports one or more errors."""

    _attr_name = "Problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_problem"

    @property
    def is_on(self) -> bool:
        errors = self.coordinator.data.get("error_list") or []
        return len(errors) > 0

    @property
    def extra_state_attributes(self) -> dict:
        return {"errors": self.coordinator.data.get("error_list") or []}
