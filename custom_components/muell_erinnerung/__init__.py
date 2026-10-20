"""Müll-Erinnerung integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CARD_URL,
    CONF_DASHBOARD_URL,
    CONF_ITEMS,
    CONF_NOTIFY,
    CONF_SNOOZE,
    CONF_TIME,
    DEFAULT_ATTR,
    DEFAULT_DASHBOARD_URL,
    DEFAULT_SNOOZE,
    DEFAULT_TIME,
    DOMAIN,
    ENTITY_KEYS,
    ENTITY_PREFIX,
    PLATFORMS,
    STORAGE_KEY,
    STORAGE_VERSION,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # Eigene Lovelace-Karte ausliefern und automatisch im Frontend laden.
    card_path = Path(__file__).parent / "frontend" / "muell-erinnerung.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_path), True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}")
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version == 1:
        # Bestehende Entitäten auf das Präfix "muellerinnerung_" umbenennen.
        registry = er.async_get(hass)
        for platform, key in ENTITY_KEYS:
            entity_id = registry.async_get_entity_id(platform, DOMAIN, f"{DOMAIN}_{key}")
            new_entity_id = f"{platform}.{ENTITY_PREFIX}_{key}"
            if entity_id and entity_id != new_entity_id and registry.async_get(new_entity_id) is None:
                registry.async_update_entity(entity_id, new_entity_id=new_entity_id)
        hass.config_entries.async_update_entry(entry, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = {**entry.data, **entry.options}
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load() or {}
    reminder_time = dt_util.parse_time(str(config.get(CONF_TIME, DEFAULT_TIME))) or dt_util.parse_time(DEFAULT_TIME)
    runtime = {
        "items": config.get(CONF_ITEMS, []),
        "reminder_time": reminder_time,
        "snooze_minutes": int(config.get(CONF_SNOOZE, DEFAULT_SNOOZE)),
        "notify_service": config.get(CONF_NOTIFY, ""),
        "dashboard_url": config.get(CONF_DASHBOARD_URL, DEFAULT_DASHBOARD_URL),
        "store": store,
        "stored": stored,
        "dismissed_date": stored.get("dismissed_date", ""),
        "snooze_until": None,
        "is_open": False,
        "last_items": [],
        "unsub_snooze": None,
        "signal": f"{DOMAIN}_{entry.entry_id}_update",
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    async def on_trigger(*_):
        await async_evaluate(hass, runtime, notify=True)

    async def on_midnight(*_):
        await async_evaluate(hass, runtime)

    entry.async_on_unload(async_track_time_change(
        hass, on_trigger, hour=reminder_time.hour, minute=reminder_time.minute, second=reminder_time.second
    ))
    entry.async_on_unload(async_track_time_change(hass, on_midnight, hour=0, minute=0, second=0))
    source_entities = [item["entity_id"] for item in runtime["items"] if item.get("entity_id")]
    if source_entities:
        entry.async_on_unload(async_track_state_change_event(hass, source_entities, on_trigger))
    entry.async_on_unload(lambda: _cancel_snooze(runtime))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    # Offene Erinnerung nach einem Neustart wiederherstellen, ohne erneut zu pushen.
    await async_evaluate(hass, runtime)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def get_due_items(hass: HomeAssistant, runtime: dict) -> list[str]:
    due = []
    for item in runtime.get("items", []):
        entity_id = item.get("entity_id", "")
        attr = item.get("attribute", DEFAULT_ATTR)
        expected = str(item.get("value", "1"))
        label = item.get("label", entity_id)
        state = hass.states.get(entity_id) if entity_id else None
        if state is None:
            continue
        # Leeres Attribut oder "state" vergleicht den Zustand der Entität selbst.
        actual = state.state if attr in (None, "", "state") else state.attributes.get(attr)
        if actual is not None and str(actual) == expected:
            due.append(label)
    return due


async def async_evaluate(hass: HomeAssistant, runtime: dict, notify: bool = False) -> None:
    """Popup-Zustand neu berechnen und Entitäten aktualisieren."""
    now = dt_util.now()
    due = get_due_items(hass, runtime)
    was_open = runtime["is_open"]
    snooze_until = runtime["snooze_until"]
    runtime["last_items"] = due
    runtime["is_open"] = (
        bool(due)
        and runtime["dismissed_date"] != now.date().isoformat()
        and not (snooze_until and now < snooze_until)
        and now.time() >= runtime["reminder_time"]
    )
    if notify and runtime["is_open"] and not was_open:
        await send_notification(hass, runtime, due)
    async_dispatcher_send(hass, runtime["signal"])


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
            "data": {"url": runtime.get("dashboard_url", DEFAULT_DASHBOARD_URL)},
        }, blocking=False)
    except Exception:
        _LOGGER.exception("Müll-Erinnerung: Benachrichtigung fehlgeschlagen")


def _cancel_snooze(runtime: dict) -> None:
    if runtime.get("unsub_snooze"):
        runtime["unsub_snooze"]()
        runtime["unsub_snooze"] = None


async def async_snooze(hass: HomeAssistant, runtime: dict) -> None:
    minutes = max(1, int(runtime.get("snooze_minutes", DEFAULT_SNOOZE)))
    when = dt_util.now() + timedelta(minutes=minutes)
    runtime["snooze_until"] = when
    _cancel_snooze(runtime)

    async def snooze_expired(now):
        runtime["unsub_snooze"] = None
        runtime["snooze_until"] = None
        await async_evaluate(hass, runtime, notify=True)

    runtime["unsub_snooze"] = async_track_point_in_time(hass, snooze_expired, when)
    await async_evaluate(hass, runtime)


async def async_mark_done(hass: HomeAssistant, runtime: dict) -> None:
    today = dt_util.now().date().isoformat()
    runtime["dismissed_date"] = today
    runtime["stored"]["dismissed_date"] = today
    await runtime["store"].async_save(runtime["stored"])
    runtime["snooze_until"] = None
    _cancel_snooze(runtime)
    await async_evaluate(hass, runtime)
