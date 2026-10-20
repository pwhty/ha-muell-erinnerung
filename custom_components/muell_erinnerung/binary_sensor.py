"""Binary sensor platform."""
from homeassistant.components.binary_sensor import BinarySensorEntity

from .coordinator import MuellConfigEntry, MuellCoordinator
from .entity import MuellEntity


async def async_setup_entry(hass, entry: MuellConfigEntry, async_add_entities):
    async_add_entities([MuellActiveSensor(entry.runtime_data)])


class MuellActiveSensor(MuellEntity, BinarySensorEntity):
    """Trigger für das Erinnerungs-Popup."""

    _attr_name = "Aktiv"
    _attr_icon = "mdi:bell-alert"

    def __init__(self, coordinator: MuellCoordinator):
        super().__init__(coordinator, "binary_sensor", "aktiv")

    @property
    def is_on(self):
        return self.coordinator.is_open
