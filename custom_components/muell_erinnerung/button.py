"""Button platform."""
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN
from . import async_snooze, async_mark_done


async def async_setup_entry(hass, entry, async_add_entities):
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        MuellButton(hass, runtime, "spaeter", "Später", "mdi:clock-outline"),
        MuellButton(hass, runtime, "erledigt", "Erledigt", "mdi:check-circle"),
        TestNotificationButton(hass, runtime),
    ])


class MuellButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, hass, runtime, key, name, icon):
        self.hass = hass
        self.runtime = runtime
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{key}"

    async def async_press(self):
        if self._key == "spaeter":
            await async_snooze(self.hass, self.runtime)
        else:
            await async_mark_done(self.hass, self.runtime)


class TestNotificationButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Testbenachrichtigung"
    _attr_icon = "mdi:message-badge"

    def __init__(self, hass, runtime):
        self.hass = hass
        self.runtime = runtime
        self._attr_unique_id = f"{DOMAIN}_testbenachrichtigung"

    async def async_press(self):
        await self.runtime["notify"]()
