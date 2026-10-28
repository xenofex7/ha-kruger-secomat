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

from .const import DOMAIN, HUMIDITY_LEVELS, OPERATING_MODES, SECOMAT_STATES
from .coordinator import SecomatCoordinator
from .entity import SecomatEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secomat sensors."""
    coordinator: SecomatCoordinator = hass.data[DOMAIN][entry.entry_id]
    serial = entry.unique_id

    entities = [
        SecomatTemperatureSensor(coordinator, serial),
        SecomatHumiditySensor(coordinator, serial),
        SecomatStateSensor(coordinator, serial),
        SecomatModeSensor(coordinator, serial),
        SecomatFirmwareSensor(coordinator, serial),
        SecomatTargetMoistureSensor(coordinator, serial),
        SecomatErrorCountSensor(coordinator, serial),
        SecomatNextStartSensor(coordinator, serial),
        SecomatDeviceTickSensor(coordinator, serial),
    ]

    async_add_entities(entities)


class SecomatTemperatureSensor(SecomatEntity, SensorEntity):
    """Secomat temperature sensor."""

    _attr_name = "Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1
    _key = "temperature"

    @property
    def native_value(self) -> float | None:
        """Return the temperature."""
        return self.coordinator.data.get("ambient_temperature")


class SecomatHumiditySensor(SecomatEntity, SensorEntity):
    """Secomat humidity sensor."""

    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _key = "humidity"

    @property
    def native_value(self) -> float | None:
        """Return the humidity."""
        return self.coordinator.data.get("humidity")


class SecomatStateSensor(SecomatEntity, SensorEntity):
    """Secomat state sensor."""

    _attr_name = "State"
    _attr_icon = "mdi:air-humidifier"
    _key = "state"

    @property
    def native_value(self) -> str | None:
        """Return the device state."""
        state = self.coordinator.data.get("secomat_state")
        if state is None:
            return None
        return SECOMAT_STATES.get(state, f"unknown ({state})")


class SecomatModeSensor(SecomatEntity, SensorEntity):
    """Secomat operating mode sensor."""

    _attr_name = "Operating Mode"
    _attr_icon = "mdi:cog"
    _key = "operating_mode"

    @property
    def native_value(self) -> str | None:
        """Return the operating mode."""
        mode = self.coordinator.data.get("operating_mode")
        if mode is None:
            return None
        return OPERATING_MODES.get(mode, f"unknown ({mode})")


class SecomatFirmwareSensor(SecomatEntity, SensorEntity):
    """Secomat firmware sensor."""

    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _key = "firmware"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        return self.coordinator.data.get("fw_version")


class SecomatTargetMoistureSensor(SecomatEntity, SensorEntity):
    """Secomat target moisture sensor (read-only)."""

    _attr_name = "Target Moisture"
    _attr_icon = "mdi:water-percent"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _key = "target_moisture"

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


class SecomatErrorCountSensor(SecomatEntity, SensorEntity):
    """Number of active errors reported by the device."""

    _attr_name = "Error Count"
    _attr_icon = "mdi:alert-circle"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _key = "error_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("error_list") or [])

    @property
    def extra_state_attributes(self) -> dict:
        return {"errors": self.coordinator.data.get("error_list") or []}


class SecomatNextStartSensor(SecomatEntity, SensorEntity):
    """Next scheduled program start (None when no timer set)."""

    _attr_name = "Next Start"
    _attr_icon = "mdi:timer-play-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _key = "next_start"

    @property
    def native_value(self) -> datetime | None:
        raw = self.coordinator.data.get("next_start")
        if not raw:
            return None
        try:
            # Device sends ISO-8601 with 'Z' suffix; drop millisecond jitter.
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.replace(microsecond=0)
        except (ValueError, AttributeError):
            return None


class SecomatDeviceTickSensor(SecomatEntity, SensorEntity):
    """Raw device clock/tick reported in the `now` field."""

    _attr_name = "Device Tick"
    _attr_icon = "mdi:clock-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _key = "device_tick"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("now")
