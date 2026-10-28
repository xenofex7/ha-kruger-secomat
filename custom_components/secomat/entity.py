"""Base entity for Krüger Secomat."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SecomatCoordinator


class SecomatEntity(CoordinatorEntity[SecomatCoordinator]):
    """Base class for all Secomat entities."""

    _attr_has_entity_name = True
    _key: str

    def __init__(self, coordinator: SecomatCoordinator, serial: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{serial}_{self._key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"Secomat {serial}",
            manufacturer="Krüger",
            model="Secomat",
            serial_number=serial,
            sw_version=coordinator.data.get("fw_version"),
        )
