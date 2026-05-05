"""API client for Krüger Secomat."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import asyncio

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class SecomatAPIError(Exception):
    """Secomat API error."""


class SecomatAPI:
    """Krüger Secomat API client."""

    def __init__(self, claim_token: str, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize the API client."""
        self._claim_token = claim_token
        self._session = session
        self._own_session = session is None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    @property
    def _headers(self) -> dict[str, str]:
        """Return API headers."""
        return {
            "claim-token": self._claim_token,
            "api": "1",
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Secomat/1.0.3 HA-Integration",
        }

    async def get_state(self) -> dict[str, Any]:
        """Get current Secomat state."""
        session = await self._ensure_session()
        try:
            async with session.get(
                API_BASE_URL,
                headers=self._headers,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise SecomatAPIError(f"API returned {response.status}")
                data = await response.json()
                if data.get("type") == "STATE":
                    return data.get("payload", {})
                return data
        except aiohttp.ClientError as err:
            raise SecomatAPIError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise SecomatAPIError("Request timeout") from err

    async def send_command(self, command: str, args: dict | None = None) -> bool:
        """Send a command to the Secomat."""
        session = await self._ensure_session()
        payload = {"command": command, "args": args or {}}
        try:
            async with session.post(
                API_BASE_URL,
                headers=self._headers,
                json=payload,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise SecomatAPIError(f"API returned {response.status}")
                data = await response.json()
                return data.get("status") == "OK"
        except aiohttp.ClientError as err:
            raise SecomatAPIError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise SecomatAPIError("Request timeout") from err

    async def turn_off(self) -> bool:
        """Turn off the Secomat."""
        return await self.send_command("OFF")

    async def start_laundry_drying(self) -> bool:
        """Start laundry drying (auto mode)."""
        return await self.send_command("PRG_WASH_AUTO")

    async def start_laundry_drying_manual(self, start_time: int = 0) -> bool:
        """Start laundry drying (manual/immediate). start_time=0 means start now."""
        return await self.send_command("PRG_WASH_MANUAL_ON", {"prg_wash_starttime": start_time})

    async def cancel_pending_start(self) -> bool:
        """Cancel a pending delayed start without full OFF (discovered by @ratsch)."""
        return await self.send_command("PRG_WASH_MANUAL_OFF")

    async def set_target_moisture(self, level: int) -> bool:
        """Set target moisture level 0-3 (discovered by @ratsch via PARAMETER_CHANGE)."""
        return await self.send_command("PARAMETER_CHANGE", {"residual_moisture_target": level})

    async def set_moisture_lock(self, locked: bool) -> bool:
        """Lock or unlock the target moisture slider (discovered by @ratsch)."""
        return await self.send_command("PARAMETER_CHANGE", {"lock_residual_moisture_target": int(locked)})

    async def start_room_drying(self) -> bool:
        """Start room drying."""
        return await self.send_command("PRG_ROOM_ON")

    async def stop_room_drying(self) -> bool:
        """Stop room drying."""
        return await self.send_command("PRG_ROOM_OFF")

    async def validate_connection(self) -> bool:
        """Validate the API connection."""
        try:
            state = await self.get_state()
            return "serial_number" in state
        except SecomatAPIError:
            return False

    async def close(self) -> None:
        """Close the session."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()
