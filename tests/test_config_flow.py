from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.muell_erinnerung.const import DOMAIN, SUBENTRY_TYPE

from .conftest import CALENDAR

SETTINGS = {
    "calendar_entity": CALENDAR,
    "lookahead_days": 60,
    "reminder_time": "19:00:00",
    "snooze_minutes": 15,
    "dashboard_url": "/lovelace/0",
}


async def test_user_flow_creates_default_types(hass, calendar):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**SETTINGS, "notify_service": "handy"})
    assert result["errors"] == {"notify_service": "invalid_notify"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**SETTINGS, "create_default_types": True})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    assert entry.data["calendar_entity"] == CALENDAR
    assert "create_default_types" not in entry.data
    assert sorted(s.title for s in entry.subentries.values()) == ["Biomüll", "Gelber Sack", "Papiermüll", "Restmüll"]
    await hass.async_block_till_done()
    assert hass.states.get("sensor.muellerinnerung_biomuell")


async def test_subentry_flow_add_and_reconfigure(hass, setup_integration):
    entry = setup_integration
    result = await hass.config_entries.subentries.async_init((entry.entry_id, SUBENTRY_TYPE), context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"name": "Sperrmüll", "pattern": "sperr("})
    assert result["errors"] == {"pattern": "invalid_pattern"}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"name": "Sperrmüll", "pattern": "sperr"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert hass.states.get("sensor.muellerinnerung_sperrmuell")

    subentry = next(s for s in entry.subentries.values() if s.title == "Biomüll")
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE),
        context={"source": config_entries.SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"name": "Biomüll", "pattern": "bio|kompost"})
    assert result["type"] is FlowResultType.ABORT
    assert entry.subentries[subentry.subentry_id].data["pattern"] == "bio|kompost"


async def test_options_flow(hass, setup_integration):
    entry = setup_integration
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(result["flow_id"], {**SETTINGS, "reminder_time": "18:30:00"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["reminder_time"] == "18:30:00"
    assert entry.runtime_data.reminder_time.hour == 18
