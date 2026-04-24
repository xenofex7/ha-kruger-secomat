"""Sensor platform for Krüger Secomat."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, HUMIDITY_LEVELS, OPERATING_MODES, SECOMAT_STATES
from .coordinator import SecomatCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat sensors."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = coordinator.data.get("serial_number", "unknown")

    entities = [
        SecomatTemperatureSensor(coordinator, entry, serial),
        SecomatHumiditySensor(coordinator, entry, serial),
        SecomatStateSensor(coordinator, entry, serial),
        SecomatModeSensor(coordinator, entry, serial),
        SecomatFirmwareSensor(coordinator, entry, serial),
        SecomatTargetMoistureSensor(coordinator, entry, serial),
        SecomatErrorCountSensor(coordinator, entry, serial),
        SecomatNextStartSensor(coordinator, entry, serial),
        SecomatDeviceTickSensor(coordinator, entry, serial),
    ]

    async_add_entities(entities)


class SecomatBaseSensor(CoordinatorEntity[SecomatCoordinator], SensorEntity):
    """Base class for Secomat sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SecomatCoordinator,
        entry: ConfigEntry,
        serial: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"Secomat {serial}",
            "manufacturer": "Krüger",
            "model": "Secomat",
            "sw_version": coordinator.data.get("fw_version"),
        }


class SecomatTemperatureSensor(SecomatBaseSensor):
    """Secomat temperature sensor."""

    _attr_name = "Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the temperature."""
        val = self.coordinator.data.get("ambient_temperature")
        return round(val, 1) if val is not None else None


class SecomatHumiditySensor(SecomatBaseSensor):
    """Secomat humidity sensor."""

    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_humidity"

    @property
    def native_value(self) -> float | None:
        """Return the humidity."""
        val = self.coordinator.data.get("humidity")
        return round(val, 1) if val is not None else None


class SecomatStateSensor(SecomatBaseSensor):
    """Secomat state sensor."""

    _attr_name = "State"
    _attr_icon = "mdi:air-humidifier"

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_state"

    @property
    def native_value(self) -> str | None:
        """Return the device state."""
        state = self.coordinator.data.get("secomat_state")
        return SECOMAT_STATES.get(state, f"unknown ({state})")


class SecomatModeSensor(SecomatBaseSensor):
    """Secomat operating mode sensor."""

    _attr_name = "Operating Mode"
    _attr_icon = "mdi:cog"

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_operating_mode"

    @property
    def native_value(self) -> str | None:
        """Return the operating mode."""
        mode = self.coordinator.data.get("operating_mode")
        return OPERATING_MODES.get(mode, f"unknown ({mode})")


class SecomatFirmwareSensor(SecomatBaseSensor):
    """Secomat firmware sensor."""

    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_firmware"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        return self.coordinator.data.get("fw_version")


class SecomatTargetMoistureSensor(SecomatBaseSensor):
    """Secomat target moisture sensor (read-only)."""

    _attr_name = "Target Moisture"
    _attr_icon = "mdi:water-percent"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_target_moisture"

    @property
    def native_value(self) -> str | None:
        """Return the current target moisture level."""
        level = self.coordinator.data.get("target_humidity_level")
        if level is None:
            return None
        return HUMIDITY_LEVELS.get(level, f"unknown ({level})")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "locked": bool(self.coordinator.data.get("target_humidity_level_locked")),
        }


class SecomatErrorCountSensor(SecomatBaseSensor):
    """Number of active errors reported by the device."""

    _attr_name = "Error Count"
    _attr_icon = "mdi:alert-circle"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_error_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("error_list") or [])

    @property
    def extra_state_attributes(self) -> dict:
        return {"errors": self.coordinator.data.get("error_list") or []}


class SecomatNextStartSensor(SecomatBaseSensor):
    """Next scheduled program start (None when no timer set)."""

    _attr_name = "Next Start"
    _attr_icon = "mdi:timer-play-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_next_start"

    @property
    def native_value(self) -> datetime | None:
        raw = self.coordinator.data.get("next_start")
        if not raw or raw == 0:
            return None
        try:
            # Device sends ISO-8601 with 'Z' suffix; drop millisecond jitter.
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.replace(microsecond=0)
        except (ValueError, AttributeError):
            return None


class SecomatDeviceTickSensor(SecomatBaseSensor):
    """Raw device clock/tick reported in the `now` field."""

    _attr_name = "Device Tick"
    _attr_icon = "mdi:clock-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_device_tick"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("now")
