"""Müll-Erinnerung integration."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import CARD_URL, DOMAIN, PLATFORMS, VERSION
from .coordinator import MuellConfigEntry, MuellCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # Eigene Lovelace-Karte ausliefern und automatisch im Frontend laden.
    card_path = Path(__file__).parent / "frontend" / "muell-erinnerung.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_path), True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MuellConfigEntry) -> bool:
    _async_detach_main_device_from_subentries(hass, entry)
    coordinator = MuellCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_setup()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Änderungen an Optionen oder Mülltypen (Subentries) laden die Integration neu.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


@callback
def _async_detach_main_device_from_subentries(hass: HomeAssistant, entry: MuellConfigEntry) -> None:
    """Hauptgerät zurück in den Haupteintrag holen.

    Bis 0.3.0 hingen auch die Mülltyp-Sensoren am Hauptgerät; HA hat das Gerät
    dadurch in einen Mülltyp-Subentry verschoben.
    """
    registry = dr.async_get(hass)
    device = registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    if device is None:
        return
    subentry_ids = device.config_entries_subentries.get(entry.entry_id, set()) - {None}
    if not subentry_ids:
        return
    registry.async_update_device(device.id, add_config_entry_id=entry.entry_id, add_config_subentry_id=None)
    for subentry_id in subentry_ids:
        registry.async_update_device(device.id, remove_config_entry_id=entry.entry_id, remove_config_subentry_id=subentry_id)


async def async_unload_entry(hass: HomeAssistant, entry: MuellConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: MuellConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
