"""Data update coordinator for Krüger Secomat."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SecomatAPI, SecoматAPIError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SecomatCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Secomat data update coordinator."""

    def __init__(self, hass: HomeAssistant, api: SecomatAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Secomat API."""
        try:
            return await self.api.get_state()
        except SecoматAPIError as err:
            raise UpdateFailed(f"Error fetching Secomat data: {err}") from err
