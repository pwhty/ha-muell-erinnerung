"""Config flow for Müll-Erinnerung."""
from __future__ import annotations

import re

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigSubentryData,
    ConfigSubentryFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CALENDAR,
    CONF_CREATE_DEFAULTS,
    CONF_DASHBOARD_URL,
    CONF_ICON,
    CONF_LOOKAHEAD,
    CONF_NOTIFY,
    CONF_PATTERN,
    CONF_SNOOZE,
    CONF_TIME,
    DEFAULT_DASHBOARD_URL,
    DEFAULT_ICON,
    DEFAULT_LOOKAHEAD,
    DEFAULT_SNOOZE,
    DEFAULT_TIME,
    DEFAULT_WASTE_TYPES,
    DOMAIN,
    SUBENTRY_TYPE,
)

SETTINGS_DEFAULTS = {
    CONF_LOOKAHEAD: DEFAULT_LOOKAHEAD,
    CONF_TIME: DEFAULT_TIME,
    CONF_SNOOZE: DEFAULT_SNOOZE,
    CONF_DASHBOARD_URL: DEFAULT_DASHBOARD_URL,
}

SETTINGS_SCHEMA = vol.Schema({
    vol.Required(CONF_CALENDAR): selector.EntitySelector(selector.EntitySelectorConfig(domain="calendar")),
    vol.Required(CONF_LOOKAHEAD): selector.NumberSelector(
        selector.NumberSelectorConfig(min=7, max=365, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="d")
    ),
    vol.Required(CONF_TIME): selector.TimeSelector(),
    vol.Required(CONF_SNOOZE): selector.NumberSelector(
        selector.NumberSelectorConfig(min=1, max=1440, step=1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="min")
    ),
    vol.Optional(CONF_NOTIFY): selector.TextSelector(),
    vol.Required(CONF_DASHBOARD_URL): selector.TextSelector(),
})

WASTE_TYPE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): selector.TextSelector(),
    vol.Required(CONF_PATTERN): selector.TextSelector(),
    vol.Optional(CONF_ICON, default=DEFAULT_ICON): selector.IconSelector(),
})


def _validate_settings(user_input: dict) -> tuple[dict, dict]:
    errors = {}
    data = dict(user_input)
    data.pop(CONF_CREATE_DEFAULTS, None)
    data[CONF_LOOKAHEAD] = int(data[CONF_LOOKAHEAD])
    data[CONF_SNOOZE] = int(data[CONF_SNOOZE])
    data[CONF_NOTIFY] = (data.get(CONF_NOTIFY) or "").strip()
    if data[CONF_NOTIFY] and not data[CONF_NOTIFY].startswith("notify."):
        errors[CONF_NOTIFY] = "invalid_notify"
    return data, errors


def _validate_pattern(pattern: str) -> dict:
    try:
        re.compile(pattern)
    except re.error:
        return {CONF_PATTERN: "invalid_pattern"}
    return {}


class MuellErinnerungConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            data, errors = _validate_settings(user_input)
            if not errors:
                subentries = [
                    ConfigSubentryData(
                        subentry_type=SUBENTRY_TYPE,
                        title=wt["name"],
                        data={CONF_PATTERN: wt[CONF_PATTERN], CONF_ICON: wt[CONF_ICON]},
                        unique_id=None,
                    )
                    for wt in DEFAULT_WASTE_TYPES
                ] if user_input.get(CONF_CREATE_DEFAULTS) else []
                return self.async_create_entry(title="Müll-Erinnerung", data=data, subentries=subentries)
        schema = SETTINGS_SCHEMA.extend({vol.Required(CONF_CREATE_DEFAULTS, default=True): selector.BooleanSelector()})
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or SETTINGS_DEFAULTS),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return MuellErinnerungOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry):
        return {SUBENTRY_TYPE: WasteTypeSubentryFlow}


class MuellErinnerungOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            data, errors = _validate_settings(user_input)
            if not errors:
                return self.async_create_entry(title="", data=data)
        current = user_input or {**SETTINGS_DEFAULTS, **self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(SETTINGS_SCHEMA, current),
            errors=errors,
        )


class WasteTypeSubentryFlow(ConfigSubentryFlow):
    """Mülltyp anlegen/ändern: Name + Suchmuster für den Kalendertermin-Titel."""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = _validate_pattern(user_input[CONF_PATTERN])
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={CONF_PATTERN: user_input[CONF_PATTERN], CONF_ICON: user_input.get(CONF_ICON) or DEFAULT_ICON},
                )
        return self._show_form("user", user_input or {}, errors)

    async def async_step_reconfigure(self, user_input=None):
        subentry = self._get_reconfigure_subentry()
        errors = {}
        if user_input is not None:
            errors = _validate_pattern(user_input[CONF_PATTERN])
            if not errors:
                return self.async_update_and_abort(
                    self._get_entry(),
                    subentry,
                    title=user_input[CONF_NAME],
                    data={CONF_PATTERN: user_input[CONF_PATTERN], CONF_ICON: user_input.get(CONF_ICON) or DEFAULT_ICON},
                )
        current = user_input or {CONF_NAME: subentry.title, **subentry.data}
        return self._show_form("reconfigure", current, errors)

    def _show_form(self, step_id: str, current: dict, errors: dict):
        # Vorhandene Termintitel als Hilfe für das Suchmuster anzeigen.
        entry = self._get_entry()
        coordinator = getattr(entry, "runtime_data", None)
        summaries = coordinator.event_summaries() if coordinator else []
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(WASTE_TYPE_SCHEMA, current),
            errors=errors,
            description_placeholders={"termine": ", ".join(summaries) or "–"},
        )
