"""Sensor platform."""
from homeassistant.components.sensor import SensorEntity

from .const import CONF_ICON
from .coordinator import MuellConfigEntry, MuellCoordinator
from .entity import MuellEntity
from .pickup import slugify_name


async def async_setup_entry(hass, entry: MuellConfigEntry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([MuellDueSensor(coordinator)])
    for subentry_id, waste_type in coordinator.waste_types.items():
        async_add_entities([WasteTypeSensor(coordinator, subentry_id, waste_type)], config_subentry_id=subentry_id)


class WasteTypeSensor(MuellEntity, SensorEntity):
    """Nächste Abholung eines Mülltyps, z. B. sensor.muellerinnerung_biomuell."""

    def __init__(self, coordinator: MuellCoordinator, subentry_id: str, waste_type: dict):
        super().__init__(coordinator, "sensor", slugify_name(waste_type["name"]), subentry_id)
        self._subentry_id = subentry_id
        self._attr_name = waste_type["name"]
        self._attr_icon = waste_type[CONF_ICON]

    @property
    def native_value(self):
        return self.coordinator.pickup(self._subentry_id).days

    @property
    def extra_state_attributes(self):
        pickup = self.coordinator.pickup(self._subentry_id)
        return {
            "anzahl_tage": pickup.days,
            "anzeige": pickup.text,
            "date": pickup.date.isoformat() if pickup.date else None,
        }


class MuellDueSensor(MuellEntity, SensorEntity):
    """Müllarten, die morgen abgeholt werden."""

    _attr_name = "Nächste Abholung"
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator: MuellCoordinator):
        super().__init__(coordinator, "sensor", "naechste_abholung")

    @property
    def native_value(self):
        return ", ".join(self.coordinator.due_tomorrow()) or "Keine"

    @property
    def extra_state_attributes(self):
        snooze_until = self.coordinator.snooze_until
        return {
            "muellarten": self.coordinator.due_tomorrow(),
            "popup_aktiv": self.coordinator.is_open,
            "erledigt_am": self.coordinator.dismissed_date,
            "schlummer_bis": snooze_until.isoformat() if snooze_until else None,
        }
