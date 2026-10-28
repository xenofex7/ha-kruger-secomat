"""API client for Krüger Secomat."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    CMD_OFF,
    CMD_PARAMETER_CHANGE,
    CMD_ROOM_OFF,
    CMD_ROOM_ON,
    CMD_WASH_AUTO,
    CMD_WASH_MANUAL_ON,
)


class SecomatAPIError(Exception):
    """Secomat API error."""


class SecomatAuthError(SecomatAPIError):
    """Claim token rejected by the Secomat cloud."""


class SecomatAPI:
    """Krüger Secomat API client."""

    def __init__(self, claim_token: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._claim_token = claim_token
        self._session = session

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
        try:
            async with self._session.get(
                API_BASE_URL,
                headers=self._headers,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (401, 403):
                    raise SecomatAuthError(f"API returned {response.status}")
                if response.status != 200:
                    raise SecomatAPIError(f"API returned {response.status}")
                data = await response.json()
                if not isinstance(data, dict) or data.get("type") != "STATE" or "payload" not in data:
                    raise SecomatAPIError(f"Unexpected response: {data}")
                return data["payload"]
        except aiohttp.ClientError as err:
            raise SecomatAPIError(f"Connection error: {err}") from err
        except ValueError as err:
            raise SecomatAPIError(f"Invalid response: {err}") from err
        except asyncio.TimeoutError as err:
            raise SecomatAPIError("Request timeout") from err

    async def send_command(self, command: str, args: dict | None = None) -> None:
        """Send a command to the Secomat."""
        payload = {"command": command, "args": args or {}}
        try:
            async with self._session.post(
                API_BASE_URL,
                headers=self._headers,
                json=payload,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise SecomatAPIError(f"API returned {response.status}")
                data = await response.json()
                if not isinstance(data, dict) or data.get("status") != "OK":
                    raise SecomatAPIError(f"Command {command} rejected: {data}")
        except aiohttp.ClientError as err:
            raise SecomatAPIError(f"Connection error: {err}") from err
        except ValueError as err:
            raise SecomatAPIError(f"Invalid response: {err}") from err
        except asyncio.TimeoutError as err:
            raise SecomatAPIError("Request timeout") from err

    async def turn_off(self) -> None:
        """Turn off the Secomat."""
        await self.send_command(CMD_OFF)

    async def start_laundry_drying(self) -> None:
        """Start laundry drying (auto mode)."""
        await self.send_command(CMD_WASH_AUTO)

    async def start_laundry_drying_manual(self, delay_seconds: int = 0) -> None:
        """Start laundry drying (manual mode).

        delay_seconds is the number of seconds from now until the program
        should start; 0 means start immediately. (Verified on hardware: the
        device interprets the value as a relative delay, not a Unix epoch
        timestamp. The iOS app's main drying button sends 0.)
        """
        await self.send_command(
            CMD_WASH_MANUAL_ON, {"prg_wash_starttime": delay_seconds}
        )

    async def set_target_moisture(self, level: int) -> None:
        """Set target moisture level 0-3 (discovered by @ratsch via PARAMETER_CHANGE)."""
        await self.send_command(CMD_PARAMETER_CHANGE, {"residual_moisture_target": level})

    async def set_moisture_lock(self, locked: bool) -> None:
        """Lock or unlock the target moisture slider (discovered by @ratsch)."""
        await self.send_command(CMD_PARAMETER_CHANGE, {"lock_residual_moisture_target": int(locked)})

    async def start_room_drying(self) -> None:
        """Start room drying."""
        await self.send_command(CMD_ROOM_ON)

    async def stop_room_drying(self) -> None:
        """Stop room drying."""
        await self.send_command(CMD_ROOM_OFF)
