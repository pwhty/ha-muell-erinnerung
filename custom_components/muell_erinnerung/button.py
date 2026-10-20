"""Button platform."""
from homeassistant.components.button import ButtonEntity

from . import async_mark_done, async_snooze, get_due_items, send_notification
from .const import DOMAIN
from .entity import MuellEntity


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        MuellButton(entry, runtime, "spaeter", "Später", "mdi:clock-outline"),
        MuellButton(entry, runtime, "erledigt", "Erledigt", "mdi:check-circle"),
        MuellButton(entry, runtime, "testbenachrichtigung", "Testbenachrichtigung", "mdi:message-badge"),
    ])


class MuellButton(MuellEntity, ButtonEntity):
    def __init__(self, entry, runtime, key, name, icon):
        super().__init__(entry, runtime, "button", key)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon

    async def async_press(self):
        if self._key == "spaeter":
            await async_snooze(self.hass, self.runtime)
        elif self._key == "erledigt":
            await async_mark_done(self.hass, self.runtime)
        else:
            await send_notification(self.hass, self.runtime, get_due_items(self.hass, self.runtime))
