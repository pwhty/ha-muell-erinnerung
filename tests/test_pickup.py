from datetime import date

from custom_components.muell_erinnerung.pickup import Event, Pickup, next_pickup, parse_event_start, slugify_name

TODAY = date(2026, 10, 20)


def test_next_pickup_picks_earliest_matching_event():
    events = [
        Event(date(2026, 10, 19), "Biomüll"),  # Vergangenheit
        Event(date(2026, 10, 30), "Biotonne"),
        Event(date(2026, 10, 21), "BIOMÜLL"),
        Event(date(2026, 10, 22), "Restabfall"),
    ]
    assert next_pickup(events, "bio", TODAY) == Pickup(date(2026, 10, 21), 1)
    assert next_pickup(events, "restmüll|restabfall", TODAY).days == 2
    assert next_pickup(events, "gelb", TODAY) == Pickup()


def test_pickup_text():
    assert Pickup().text == "unbekannt"
    assert Pickup(TODAY, 0).text == "Heute"
    assert Pickup(TODAY, 1).text == "Morgen"
    assert Pickup(TODAY, 5).text == "In 5 Tagen"


def test_parse_event_start():
    assert parse_event_start("2026-10-21") == date(2026, 10, 21)
    assert parse_event_start("2026-10-21T06:00:00") == date(2026, 10, 21)
    assert parse_event_start(None) is None


def test_slugify_name():
    assert slugify_name("Biomüll") == "biomuell"
    assert slugify_name("Gelber Sack") == "gelber_sack"
