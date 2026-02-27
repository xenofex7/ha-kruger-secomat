"""Sensor platform for Krüger Secomat."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OPERATING_MODES, SECOMAT_STATES
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
    _attr_entity_category = "diagnostic"

    def __init__(self, coordinator, entry, serial):
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_firmware"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        return self.coordinator.data.get("fw_version")
