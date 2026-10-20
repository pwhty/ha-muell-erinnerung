"""Button platform."""
from homeassistant.components.button import ButtonEntity

from .coordinator import MuellConfigEntry, MuellCoordinator
from .entity import MuellEntity


async def async_setup_entry(hass, entry: MuellConfigEntry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([
        MuellButton(coordinator, "spaeter", "Später", "mdi:clock-outline", coordinator.async_snooze),
        MuellButton(coordinator, "erledigt", "Erledigt", "mdi:check-circle", coordinator.async_mark_done),
        MuellButton(coordinator, "testbenachrichtigung", "Testbenachrichtigung", "mdi:message-badge", coordinator.async_send_notification),
    ])


class MuellButton(MuellEntity, ButtonEntity):
    def __init__(self, coordinator: MuellCoordinator, key, name, icon, action):
        super().__init__(coordinator, "button", key)
        self._attr_name = name
        self._attr_icon = icon
        self._action = action

    async def async_press(self):
        await self._action()
