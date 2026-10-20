"""Kalenderabruf und Erinnerungslogik."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_point_in_time, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CALENDAR,
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
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    SUBENTRY_TYPE,
    UPDATE_INTERVAL,
)
from .pickup import Event, Pickup, next_pickup, parse_event_start

_LOGGER = logging.getLogger(__name__)

type MuellConfigEntry = ConfigEntry[MuellCoordinator]


class MuellCoordinator(DataUpdateCoordinator[list[Event]]):
    """Hält die Kalendertermine und den Zustand des Erinnerungs-Popups."""

    config_entry: MuellConfigEntry

    def __init__(self, hass: HomeAssistant, entry: MuellConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        config = {**entry.data, **entry.options}
        self.calendar: str = config[CONF_CALENDAR]
        self.lookahead_days = int(config.get(CONF_LOOKAHEAD, DEFAULT_LOOKAHEAD))
        self.reminder_time = dt_util.parse_time(str(config.get(CONF_TIME, DEFAULT_TIME))) or dt_util.parse_time(DEFAULT_TIME)
        self.snooze_minutes = max(1, int(config.get(CONF_SNOOZE, DEFAULT_SNOOZE)))
        self.notify_service: str = config.get(CONF_NOTIFY, "")
        self.dashboard_url: str = config.get(CONF_DASHBOARD_URL, DEFAULT_DASHBOARD_URL)
        self.waste_types = {
            subentry_id: {"name": sub.title, CONF_PATTERN: sub.data[CONF_PATTERN], CONF_ICON: sub.data.get(CONF_ICON) or DEFAULT_ICON}
            for subentry_id, sub in entry.subentries.items()
            if sub.subentry_type == SUBENTRY_TYPE
        }
        self.dismissed_date = ""
        self.snooze_until = None
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._unsub_snooze = None

    # --- Kalender ---------------------------------------------------------

    async def _async_update_data(self) -> list[Event]:
        if self.hass.states.get(self.calendar) is None:
            raise UpdateFailed(f"Kalender {self.calendar} ist (noch) nicht verfügbar")
        start = dt_util.start_of_local_day()
        end = start + timedelta(days=self.lookahead_days + 1)
        try:
            response = await self.hass.services.async_call(
                "calendar",
                "get_events",
                {"start_date_time": start.isoformat(), "end_date_time": end.isoformat()},
                target={"entity_id": self.calendar},
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError as err:
            raise UpdateFailed(f"Kalender {self.calendar} nicht abrufbar: {err}") from err
        events = []
        for raw in (response or {}).get(self.calendar, {}).get("events", []):
            start_date = parse_event_start(raw.get("start"))
            if start_date:
                events.append(Event(start_date, raw.get("summary") or ""))
        return events

    def pickup(self, subentry_id: str) -> Pickup:
        return next_pickup(self.data or [], self.waste_types[subentry_id][CONF_PATTERN], dt_util.now().date())

    def due_tomorrow(self) -> list[str]:
        return [wt["name"] for sid, wt in self.waste_types.items() if self.pickup(sid).days == 1]

    def event_summaries(self) -> list[str]:
        return sorted({e.summary for e in self.data or [] if e.summary})

    # --- Erinnerung -------------------------------------------------------

    @property
    def is_open(self) -> bool:
        now = dt_util.now()
        return (
            bool(self.due_tomorrow())
            and self.dismissed_date != now.date().isoformat()
            and not (self.snooze_until and now < self.snooze_until)
            and now.time() >= self.reminder_time
        )

    async def async_setup(self) -> None:
        """Gespeicherten Zustand laden und Zeit-Trigger registrieren."""
        stored = await self._store.async_load() or {}
        self.dismissed_date = stored.get("dismissed_date", "")
        t = self.reminder_time
        entry = self.config_entry
        entry.async_on_unload(async_track_time_change(
            self.hass, self._on_reminder_time, hour=t.hour, minute=t.minute, second=t.second
        ))
        # Nach Mitternacht Termine neu laden, damit Tage und "Morgen" stimmen.
        entry.async_on_unload(async_track_time_change(self.hass, self._on_midnight, hour=0, minute=0, second=5))
        entry.async_on_unload(self._cancel_snooze)

    async def _on_reminder_time(self, _now) -> None:
        await self._async_open_if_due()

    async def _on_midnight(self, _now) -> None:
        await self.async_refresh()

    async def _async_open_if_due(self) -> None:
        if self.is_open:
            await self.async_send_notification()
        self.async_update_listeners()

    async def async_snooze(self) -> None:
        self.snooze_until = dt_util.now() + timedelta(minutes=self.snooze_minutes)
        self._cancel_snooze()
        self._unsub_snooze = async_track_point_in_time(self.hass, self._on_snooze_expired, self.snooze_until)
        self.async_update_listeners()

    async def _on_snooze_expired(self, _now) -> None:
        self._unsub_snooze = None
        self.snooze_until = None
        await self._async_open_if_due()

    async def async_mark_done(self) -> None:
        self.dismissed_date = dt_util.now().date().isoformat()
        await self._store.async_save({"dismissed_date": self.dismissed_date})
        self.snooze_until = None
        self._cancel_snooze()
        self.async_update_listeners()

    def _cancel_snooze(self) -> None:
        if self._unsub_snooze:
            self._unsub_snooze()
            self._unsub_snooze = None

    async def async_send_notification(self) -> None:
        due = self.due_tomorrow()
        if not self.notify_service or not due:
            return
        domain, _, service = self.notify_service.partition(".")
        message = "Folgende Müllarten müssen für die morgige Abholung rausgestellt werden: " + ", ".join(due)
        try:
            await self.hass.services.async_call(domain, service, {
                "title": "Müllabholung morgen",
                "message": message,
                "data": {"url": self.dashboard_url},
            }, blocking=False)
        except HomeAssistantError:
            _LOGGER.exception("Benachrichtigung über %s fehlgeschlagen", self.notify_service)
