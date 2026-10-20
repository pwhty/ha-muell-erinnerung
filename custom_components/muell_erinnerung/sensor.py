"""Sensor platform."""
from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .entity import MuellEntity


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuellDueSensor(entry, runtime)])


class MuellDueSensor(MuellEntity, SensorEntity):
    _attr_name = "Nächste Abholung"
    _attr_icon = "mdi:trash-can"

    def __init__(self, entry, runtime):
        super().__init__(entry, runtime, "sensor", "naechste_abholung")

    @property
    def native_value(self):
        return ", ".join(self.runtime.get("last_items") or []) or "Keine"

    @property
    def extra_state_attributes(self):
        snooze_until = self.runtime.get("snooze_until")
        return {
            "muellarten": self.runtime.get("last_items", []),
            "popup_aktiv": self.runtime.get("is_open", False),
            "erledigt_am": self.runtime.get("dismissed_date", ""),
            "schlummer_bis": snooze_until.isoformat() if snooze_until else None,
        }
