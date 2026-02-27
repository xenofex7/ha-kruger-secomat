"""Config flow for Krüger Secomat."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import SecomatAPI
from .const import CONF_CLAIM_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SecomatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Secomat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            claim_token = user_input[CONF_CLAIM_TOKEN]
            api = SecomatAPI(claim_token)

            try:
                valid = await api.validate_connection()
                if valid:
                    state = await api.get_state()
                    serial = state.get("serial_number", "unknown")
                    await api.close()

                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Secomat {serial}",
                        data={CONF_CLAIM_TOKEN: claim_token},
                    )
                else:
                    errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLAIM_TOKEN): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "instructions": "Enter the claim token from your Secomat app. "
                "You can obtain it by intercepting the app traffic with mitmproxy."
            },
        )
