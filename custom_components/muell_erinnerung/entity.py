"""Gemeinsame Basis für alle Müll-Erinnerung-Entitäten."""
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DEVICE_NAME, DOMAIN, ENTITY_PREFIX, VERSION


class MuellEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry, runtime, platform, key):
        self.runtime = runtime
        self._attr_unique_id = f"{DOMAIN}_{key}"
        # Feste Entity-ID, unabhängig von Name/Umlauten: <plattform>.muellerinnerung_<key>
        self.entity_id = f"{platform}.{ENTITY_PREFIX}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEVICE_NAME,
            entry_type=DeviceEntryType.SERVICE,
            sw_version=VERSION,
        )

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.runtime["signal"], self.async_write_ha_state)
        )
