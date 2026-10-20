"""Fixtures: Test-Kalender und eingerichtete Integration."""
from datetime import date, datetime, timedelta

import pytest
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.components.calendar.const import DATA_COMPONENT
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.muell_erinnerung.const import (
    CONF_CALENDAR,
    CONF_ICON,
    CONF_PATTERN,
    DEFAULT_WASTE_TYPES,
    DOMAIN,
    SUBENTRY_TYPE,
)

CALENDAR = "calendar.abfall"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def mock_frontend(hass):
    """Frontend ohne hass_frontend-Paket: nur als geladen markieren."""
    from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL

    hass.config.components.add("frontend")
    hass.data[DATA_EXTRA_MODULE_URL] = set()


class FakeCalendar(CalendarEntity):
    _attr_name = "Abfall"

    def __init__(self):
        self.events: list[CalendarEvent] = []

    def add(self, day: date, summary: str):
        self.events.append(CalendarEvent(start=day, end=day + timedelta(days=1), summary=summary))

    @property
    def event(self):
        return None

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime):
        return [e for e in self.events if start_date.date() <= e.start < end_date.date()]


@pytest.fixture
async def calendar(hass):
    await async_setup_component(hass, "calendar", {})
    cal = FakeCalendar()
    await hass.data[DATA_COMPONENT].async_add_entities([cal])
    await hass.async_block_till_done()
    assert hass.states.get(CALENDAR)
    return cal


@pytest.fixture
def notify_calls(hass):
    return async_mock_service(hass, "notify", "handy")


@pytest.fixture
def config_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        title="Müll-Erinnerung",
        data={CONF_CALENDAR: CALENDAR, "notify_service": "notify.handy"},
        subentries_data=[
            {
                "subentry_type": SUBENTRY_TYPE,
                "title": wt["name"],
                "data": {CONF_PATTERN: wt[CONF_PATTERN], CONF_ICON: wt[CONF_ICON]},
                "unique_id": None,
            }
            for wt in DEFAULT_WASTE_TYPES
        ],
    )


@pytest.fixture
async def setup_integration(hass, calendar, config_entry, notify_calls):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
