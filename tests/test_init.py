from datetime import date, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.muell_erinnerung.const import CONF_ICON, CONF_PATTERN, DOMAIN, SUBENTRY_TYPE


def _local(*args) -> datetime:
    return datetime(*args, tzinfo=dt_util.get_default_time_zone())


async def _press(hass, entity_id):
    await hass.services.async_call("button", "press", {"entity_id": entity_id}, blocking=True)
    await hass.async_block_till_done()


async def test_entities_from_calendar(hass: HomeAssistant, freezer: FrozenDateTimeFactory, calendar, config_entry, notify_calls):
    freezer.move_to(_local(2026, 10, 20, 10, 0))
    calendar.add(date(2026, 10, 21), "Biomüll")
    calendar.add(date(2026, 10, 21), "Gelber Sack")
    calendar.add(date(2026, 10, 27), "Altpapier")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    bio = hass.states.get("sensor.muellerinnerung_biomuell")
    assert bio.state == "1"
    assert bio.attributes["anzeige"] == "Morgen"
    assert bio.attributes["date"] == "2026-10-21"
    assert bio.attributes["icon"] == "mdi:leaf"
    assert hass.states.get("sensor.muellerinnerung_papiermuell").attributes["anzeige"] == "In 7 Tagen"
    rest = hass.states.get("sensor.muellerinnerung_restmuell")
    assert rest.state == "unknown"
    assert rest.attributes["anzeige"] == "unbekannt"
    assert hass.states.get("sensor.muellerinnerung_gelber_sack").state == "1"
    assert hass.states.get("sensor.muellerinnerung_naechste_abholung").attributes["muellarten"] == ["Biomüll", "Gelber Sack"]
    for entity_id in ("button.muellerinnerung_spaeter", "button.muellerinnerung_erledigt", "button.muellerinnerung_testbenachrichtigung"):
        assert hass.states.get(entity_id)
    # Vor der Erinnerungszeit kein Popup.
    assert hass.states.get("binary_sensor.muellerinnerung_aktiv").state == "off"


async def test_reminder_snooze_and_done(hass: HomeAssistant, freezer: FrozenDateTimeFactory, calendar, config_entry, notify_calls):
    freezer.move_to(_local(2026, 10, 20, 18, 59, 50))
    calendar.add(date(2026, 10, 21), "Biomüll")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    active = "binary_sensor.muellerinnerung_aktiv"
    assert hass.states.get(active).state == "off"

    freezer.move_to(_local(2026, 10, 20, 19, 0, 0))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(active).state == "on"
    assert len(notify_calls) == 1
    assert "Biomüll" in notify_calls[0].data["message"]

    await _press(hass, "button.muellerinnerung_spaeter")
    assert hass.states.get(active).state == "off"

    freezer.tick(timedelta(minutes=15, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(active).state == "on"
    assert len(notify_calls) == 2

    await _press(hass, "button.muellerinnerung_erledigt")
    assert hass.states.get(active).state == "off"
    assert hass.states.get("sensor.muellerinnerung_naechste_abholung").attributes["erledigt_am"] == "2026-10-20"

    # Nach Mitternacht: Abholung ist heute, keine Erinnerung; Sensor zeigt "Heute".
    freezer.move_to(_local(2026, 10, 21, 0, 0, 5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.muellerinnerung_biomuell").attributes["anzeige"] == "Heute"
    assert hass.states.get(active).state == "off"


async def test_restart_after_reminder_time_restores_popup(hass, freezer, calendar, config_entry, notify_calls):
    freezer.move_to(_local(2026, 10, 20, 21, 0))
    calendar.add(date(2026, 10, 21), "Restmüll")
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.muellerinnerung_aktiv").state == "on"
    assert notify_calls == []


async def test_add_waste_type_reloads(hass, freezer, setup_integration, calendar):
    entry = setup_integration
    calendar.add(dt_util.now().date() + timedelta(days=3), "Sperrmüll-Abholung")
    hass.config_entries.async_add_subentry(entry, _subentry("Sperrmüll", "sperr"))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.muellerinnerung_sperrmuell")
    assert state is not None
    assert state.attributes["anzeige"] == "In 3 Tagen"


def _subentry(title, pattern):
    from homeassistant.config_entries import ConfigSubentry

    return ConfigSubentry(data={CONF_PATTERN: pattern, CONF_ICON: "mdi:sofa"}, subentry_type=SUBENTRY_TYPE, title=title, unique_id=None)


async def test_missing_calendar_retries(hass, config_entry):
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state.name == "SETUP_RETRY"


async def test_each_device_belongs_to_one_subentry(hass, setup_integration):
    entry = setup_integration
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    main = devices.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert main.config_entries_subentries == {entry.entry_id: {None}}
    for entity_id in ("sensor.muellerinnerung_naechste_abholung", "binary_sensor.muellerinnerung_aktiv", "button.muellerinnerung_spaeter"):
        assert entities.async_get(entity_id).device_id == main.id
    for subentry_id, subentry in entry.subentries.items():
        device = devices.async_get_device(identifiers={(DOMAIN, subentry_id)})
        assert device.name == subentry.title
        assert device.via_device_id == main.id
        assert device.config_entries_subentries == {entry.entry_id: {subentry_id}}
    bio = hass.states.get("sensor.muellerinnerung_biomuell")
    assert bio.attributes["friendly_name"] == "Biomüll"


async def test_main_device_moved_back_from_subentry(hass, calendar, config_entry, notify_calls):
    """Zustand von 0.3.0: Hauptgerät steckt in einem Mülltyp-Subentry."""
    config_entry.add_to_hass(hass)
    subentry_id = next(iter(config_entry.subentries))
    devices = dr.async_get(hass)
    old = devices.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        config_subentry_id=subentry_id,
        identifiers={(DOMAIN, config_entry.entry_id)},
        name="Müllerinnerung",
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    main = devices.async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
    assert main.id == old.id
    assert main.config_entries_subentries == {config_entry.entry_id: {None}}
