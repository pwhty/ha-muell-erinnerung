"""Config flow for Müll-Erinnerung."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv, selector

from .const import (
    CONF_DASHBOARD_URL,
    CONF_ITEMS,
    CONF_NOTIFY,
    CONF_SNOOZE,
    CONF_TIME,
    DEFAULT_ATTR,
    DEFAULT_DASHBOARD_URL,
    DEFAULT_ITEMS,
    DEFAULT_SNOOZE,
    DEFAULT_TIME,
    DEFAULT_VALUE,
    DOMAIN,
)

ITEMS_SCHEMA = vol.All(
    [vol.Schema({
        vol.Required("label"): cv.string,
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("attribute", default=DEFAULT_ATTR): vol.Any(None, cv.string),
        vol.Optional("value", default=DEFAULT_VALUE): cv.string,
    })],
    vol.Length(min=1),
)


def _build_schema(current: dict) -> vol.Schema:
    # Die Müllarten werden als YAML-Liste im ObjectSelector bearbeitet.
    return vol.Schema({
        vol.Required(CONF_ITEMS, default=current.get(CONF_ITEMS, DEFAULT_ITEMS)): selector.ObjectSelector(),
        vol.Required(CONF_TIME, default=current.get(CONF_TIME, DEFAULT_TIME)): selector.TimeSelector(),
        vol.Required(CONF_SNOOZE, default=current.get(CONF_SNOOZE, DEFAULT_SNOOZE)): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=1440, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min")
        ),
        vol.Optional(CONF_NOTIFY, description={"suggested_value": current.get(CONF_NOTIFY, "")}): selector.TextSelector(),
        vol.Required(CONF_DASHBOARD_URL, default=current.get(CONF_DASHBOARD_URL, DEFAULT_DASHBOARD_URL)): selector.TextSelector(),
    })


def _validate(user_input: dict) -> tuple[dict, dict]:
    errors = {}
    data = dict(user_input)
    try:
        data[CONF_ITEMS] = ITEMS_SCHEMA(data.get(CONF_ITEMS))
    except vol.Invalid:
        errors[CONF_ITEMS] = "invalid_items"
    data[CONF_SNOOZE] = int(data[CONF_SNOOZE])
    data[CONF_NOTIFY] = (data.get(CONF_NOTIFY) or "").strip()
    if data[CONF_NOTIFY] and not data[CONF_NOTIFY].startswith("notify."):
        errors[CONF_NOTIFY] = "invalid_notify"
    return data, errors


class MuellErinnerungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            data, errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="Müll-Erinnerung", data=data)
        return self.async_show_form(
            step_id="user", data_schema=_build_schema(user_input or {}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MuellErinnerungOptionsFlow()


class MuellErinnerungOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            data, errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=data)
        current = user_input or {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_build_schema(current), errors=errors
        )
