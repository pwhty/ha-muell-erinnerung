"""Binary sensor platform."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN
from . import get_due_items
from homeassistant.util import dt as dt_util


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuellActiveSensor(hass, runtime)])


class MuellActiveSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Erinnerung aktiv"
    _attr_icon = "mdi:bell-alert"

    def __init__(self, hass, runtime):
        self.hass = hass
        self.runtime = runtime
        self._attr_unique_id = f"{DOMAIN}_aktiv"

    @property
    def is_on(self):
        today = dt_util.now().date().isoformat()
        return bool(get_due_items(self.hass, self.runtime)) and self.runtime.get("dismissed_today") != today
