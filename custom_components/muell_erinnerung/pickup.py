"""Berechnung der nächsten Abholung aus Kalenderterminen."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from homeassistant.util import dt as dt_util, slugify

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"})


@dataclass(frozen=True)
class Event:
    start: date
    summary: str


@dataclass(frozen=True)
class Pickup:
    date: date | None = None
    days: int | None = None

    @property
    def text(self) -> str:
        if self.days is None:
            return "unbekannt"
        if self.days == 0:
            return "Heute"
        if self.days == 1:
            return "Morgen"
        return f"In {self.days} Tagen"


def next_pickup(events: list[Event], pattern: str, today: date) -> Pickup:
    """Frühester Termin ab heute, dessen Titel auf das Muster passt (ohne Groß-/Kleinschreibung)."""
    dates = [e.start for e in events if e.start >= today and re.search(pattern, e.summary, re.IGNORECASE)]
    if not dates:
        return Pickup()
    first = min(dates)
    return Pickup(first, (first - today).days)


def parse_event_start(value: str | None) -> date | None:
    """Start aus calendar.get_events: "YYYY-MM-DD" (ganztägig) oder ISO-Zeitstempel."""
    if not value:
        return None
    if len(value) == 10:
        return dt_util.parse_date(value)
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.date()
    return dt_util.as_local(parsed).date()


def slugify_name(name: str) -> str:
    """Biomüll -> biomuell (statt biomull wie bei HA-Standard)."""
    return slugify(name.translate(_UMLAUTS))
