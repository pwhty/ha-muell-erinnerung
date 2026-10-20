"""Config flow for Müll-Erinnerung."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_ITEMS, CONF_TIME, CONF_SNOOZE, CONF_NOTIFY, CONF_DASHBOARD_URL, DEFAULT_TIME, DEFAULT_SNOOZE, DEFAULT_ATTR, DEFAULT_VALUE


class MuellErinnerungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Müll-Erinnerung", data=user_input)
        schema = vol.Schema({
            vol.Required(CONF_ITEMS, default=[
                {"label":"Papier","entity_id":"sensor.nachster_papier","attribute":DEFAULT_ATTR,"value":DEFAULT_VALUE},
                {"label":"Biomüll","entity_id":"sensor.nachster_biomull","attribute":DEFAULT_ATTR,"value":DEFAULT_VALUE},
                {"label":"Restmüll","entity_id":"sensor.nachster_restmull","attribute":DEFAULT_ATTR,"value":DEFAULT_VALUE},
                {"label":"Gelber Sack","entity_id":"sensor.nachster_gelber_sack","attribute":DEFAULT_ATTR,"value":DEFAULT_VALUE},
            ]): vol.All(list, [vol.Schema({
                vol.Required("label"): str,
                vol.Required("entity_id"): str,
                vol.Optional("attribute", default=DEFAULT_ATTR): str,
                vol.Optional("value", default=DEFAULT_VALUE): str,
            })]),
            vol.Optional(CONF_TIME, default=DEFAULT_TIME): str,
            vol.Optional(CONF_SNOOZE, default=DEFAULT_SNOOZE): vol.All(int, vol.Range(min=1, max=1440)),
            vol.Optional(CONF_NOTIFY, default=""): str,
            vol.Optional(CONF_DASHBOARD_URL, default="/lovelace/0"): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MuellErinnerungOptionsFlow(config_entry)


class MuellErinnerungOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema({
            vol.Required(CONF_ITEMS, default=current.get(CONF_ITEMS, [])): vol.All(list, [vol.Schema({
                vol.Required("label"): str,
                vol.Required("entity_id"): str,
                vol.Optional("attribute", default=DEFAULT_ATTR): str,
                vol.Optional("value", default=DEFAULT_VALUE): str,
            })]),
            vol.Optional(CONF_TIME, default=current.get(CONF_TIME, DEFAULT_TIME)): str,
            vol.Optional(CONF_SNOOZE, default=current.get(CONF_SNOOZE, DEFAULT_SNOOZE)): vol.All(int, vol.Range(min=1, max=1440)),
            vol.Optional(CONF_NOTIFY, default=current.get(CONF_NOTIFY, "")): str,
            vol.Optional(CONF_DASHBOARD_URL, default=current.get(CONF_DASHBOARD_URL, "/lovelace/0")): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
