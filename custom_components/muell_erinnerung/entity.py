"""Gemeinsame Basis für alle Müll-Erinnerung-Entitäten."""
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_NAME, DOMAIN, ENTITY_PREFIX, VERSION
from .coordinator import MuellCoordinator


class MuellEntity(CoordinatorEntity[MuellCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MuellCoordinator, platform: str, key: str, unique_key: str | None = None):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{unique_key or key}"
        # Feste Entity-ID, unabhängig von Name/Umlauten: <plattform>.muellerinnerung_<key>
        self.entity_id = f"{platform}.{ENTITY_PREFIX}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=DEVICE_NAME,
            entry_type=DeviceEntryType.SERVICE,
            sw_version=VERSION,
        )
