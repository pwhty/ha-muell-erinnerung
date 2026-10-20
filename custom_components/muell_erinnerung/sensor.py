"""Sensor platform."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuellDueSensor(runtime)])


class MuellDueSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Nächste Abholung"
    _attr_icon = "mdi:trash-can"

    def __init__(self, runtime):
        self.runtime = runtime
        self._attr_unique_id = f"{DOMAIN}_naechste_abholung"

    @property
    def native_value(self):
        return ", ".join(self.runtime.get("last_items") or []) or "Keine"

    @property
    def extra_state_attributes(self):
        return {
            "muellarten": self.runtime.get("last_items", []),
            "popup_aktiv": self.runtime.get("is_open", False),
            "erledigt_am": self.runtime.get("dismissed_today", ""),
            "schlummer_bis": self.runtime.get("snooze_until").isoformat() if self.runtime.get("snooze_until") else None,
        }
