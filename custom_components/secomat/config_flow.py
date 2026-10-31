from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SecomatAPI, SecomatAPIError, SecomatAuthError
from .const import CONF_CLAIM_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SecomatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            claim_token = user_input[CONF_CLAIM_TOKEN]
            api = SecomatAPI(claim_token, async_get_clientsession(self.hass))

            try:
                state = await api.get_state()
                serial = state["serial_number"]
            except SecomatAuthError:
                errors["base"] = "invalid_auth"
            except SecomatAPIError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured(updates={CONF_CLAIM_TOKEN: claim_token})

                return self.async_create_entry(
                    title=f"Secomat {serial}",
                    data={CONF_CLAIM_TOKEN: claim_token},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLAIM_TOKEN): str,
                }
            ),
            errors=errors,
        )
