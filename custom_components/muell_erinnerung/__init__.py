"""Müll-Erinnerung integration."""
from __future__ import annotations

from datetime import datetime, time, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, PLATFORMS, STORAGE_KEY, STORAGE_VERSION, CONF_ITEMS, CONF_TIME, CONF_SNOOZE, CONF_NOTIFY, CONF_DASHBOARD_URL, DEFAULT_TIME, DEFAULT_SNOOZE

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = dict(entry.data)
    options = dict(entry.options)
    config = {**data, **options}
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load() or {}
    runtime = {
        "items": config.get(CONF_ITEMS, []),
        "reminder_time": config.get(CONF_TIME, DEFAULT_TIME),
        "snooze_minutes": int(config.get(CONF_SNOOZE, DEFAULT_SNOOZE)),
        "notify_service": config.get(CONF_NOTIFY, ""),
        "dashboard_url": config.get(CONF_DASHBOARD_URL, "/lovelace/0"),
        "store": store,
        "stored": stored,
        "dismissed_today": stored.get("dismissed_date", ""),
        "snooze_until": None,
        "is_open": False,
        "last_items": [],
        "unsub_time": None,
        "unsub_snooze": None,
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    async def refresh_and_maybe_notify(force=False):
        now = dt_util.now()
        due = get_due_items(hass, runtime)
        today = now.date().isoformat()
        if runtime["dismissed_today"] == today:
            runtime["is_open"] = False
            return
        snooze_until = runtime.get("snooze_until")
        if snooze_until and now < snooze_until:
            return
        if due:
            runtime["last_items"] = due
            runtime["is_open"] = True
            runtime["snooze_until"] = None
            if runtime.get("notify_service") and (force or not runtime.get("notified_for_date") == today):
                await send_notification(hass, runtime, due)
                runtime["notified_for_date"] = today
        else:
            runtime["is_open"] = False

    runtime["refresh"] = refresh_and_maybe_notify

    async def at_reminder_time(now):
        await refresh_and_maybe_notify(force=True)

    try:
        hour, minute, second = [int(x) for x in runtime["reminder_time"].split(":")]
    except (ValueError, AttributeError):
        hour, minute, second = 19, 0, 0
    runtime["unsub_time"] = async_track_time_change(
        hass, at_reminder_time, hour=hour, minute=minute, second=second
    )

    async def snooze_expired(now):
        if runtime.get("snooze_until") and now >= runtime["snooze_until"]:
            runtime["snooze_until"] = None
            await refresh_and_maybe_notify(force=True)

    from homeassistant.helpers.event import async_track_point_in_time
    runtime["schedule_snooze"] = lambda when: async_track_point_in_time(hass, snooze_expired, when)
    runtime["notify"] = lambda: send_notification(hass, runtime, get_due_items(hass, runtime))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    # Recover an outstanding due reminder after a restart, without sending an immediate push.
    await refresh_and_maybe_notify(force=False)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = hass.data[DOMAIN].pop(entry.entry_id, None)
    if runtime:
        if runtime.get("unsub_time"):
            runtime["unsub_time"]()
        if runtime.get("unsub_snooze"):
            runtime["unsub_snooze"]()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def get_due_items(hass: HomeAssistant, runtime: dict) -> list[str]:
    due = []
    for item in runtime.get("items", []):
        entity_id = item.get("entity_id", "")
        attr = item.get("attribute", "anzahl_tage")
        expected = str(item.get("value", "1"))
        label = item.get("label", entity_id)
        state = hass.states.get(entity_id) if entity_id else None
        if state is None:
            continue
        actual = state.attributes.get(attr)
        if actual is not None and str(actual) == expected:
            due.append(label)
    return due


async def send_notification(hass: HomeAssistant, runtime: dict, due: list[str]) -> None:
    service = runtime.get("notify_service", "")
    if not service or not due:
        return
    if "." not in service:
        _LOGGER.warning("Notify-Ziel muss im Format notify.service_name angegeben werden")
        return
    domain, name = service.split(".", 1)
    message = "Folgende Müllarten müssen für die morgige Abholung rausgestellt werden: " + ", ".join(due)
    try:
        await hass.services.async_call(domain, name, {
            "title": "Müllabholung morgen",
            "message": message,
            "data": {"url": runtime.get("dashboard_url", "/lovelace/0")}
        }, blocking=False)
    except Exception:
        _LOGGER.exception("Müll-Erinnerung: Benachrichtigung fehlgeschlagen")


async def async_snooze(hass: HomeAssistant, runtime: dict) -> None:
    runtime["is_open"] = False
    minutes = max(1, int(runtime.get("snooze_minutes", 15)))
    when = dt_util.now() + timedelta(minutes=minutes)
    runtime["snooze_until"] = when
    if runtime.get("unsub_snooze"):
        runtime["unsub_snooze"]()
    runtime["unsub_snooze"] = runtime["schedule_snooze"](when)


async def async_mark_done(hass: HomeAssistant, runtime: dict) -> None:
    today = dt_util.now().date().isoformat()
    runtime["dismissed_today"] = today
    runtime["stored"]["dismissed_date"] = today
    await runtime["store"].async_save(runtime["stored"])
    runtime["is_open"] = False
    runtime["snooze_until"] = None
    if runtime.get("unsub_snooze"):
        runtime["unsub_snooze"]()
        runtime["unsub_snooze"] = None
