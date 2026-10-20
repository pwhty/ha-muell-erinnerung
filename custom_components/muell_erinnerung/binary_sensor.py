"""Binary sensor platform."""
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .entity import MuellEntity


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuellActiveSensor(entry, runtime)])


class MuellActiveSensor(MuellEntity, BinarySensorEntity):
    _attr_name = "Aktiv"
    _attr_icon = "mdi:bell-alert"

    def __init__(self, entry, runtime):
        super().__init__(entry, runtime, "binary_sensor", "aktiv")

    @property
    def is_on(self):
        return self.runtime.get("is_open", False)
