DOMAIN = "muell_erinnerung"
VERSION = "0.2.0"
PLATFORMS = ["sensor", "binary_sensor", "button"]
CONF_ITEMS = "items"
CONF_TIME = "reminder_time"
CONF_SNOOZE = "snooze_minutes"
CONF_NOTIFY = "notify_service"
CONF_DASHBOARD_URL = "dashboard_url"
DEFAULT_TIME = "19:00:00"
DEFAULT_SNOOZE = 15
DEFAULT_ATTR = "anzahl_tage"
DEFAULT_VALUE = "1"
DEFAULT_DASHBOARD_URL = "/lovelace/0"
DEFAULT_ITEMS = [
    {"label": "Papier", "entity_id": "sensor.nachster_papier", "attribute": DEFAULT_ATTR, "value": DEFAULT_VALUE},
    {"label": "Biomüll", "entity_id": "sensor.nachster_biomull", "attribute": DEFAULT_ATTR, "value": DEFAULT_VALUE},
    {"label": "Restmüll", "entity_id": "sensor.nachster_restmull", "attribute": DEFAULT_ATTR, "value": DEFAULT_VALUE},
    {"label": "Gelber Sack", "entity_id": "sensor.nachster_gelber_sack", "attribute": DEFAULT_ATTR, "value": DEFAULT_VALUE},
]
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_state"

# Entity-IDs: <plattform>.muellerinnerung_<key>
ENTITY_PREFIX = "muellerinnerung"
DEVICE_NAME = "Müllerinnerung"
ENTITY_KEYS = [
    ("sensor", "naechste_abholung"),
    ("binary_sensor", "aktiv"),
    ("button", "spaeter"),
    ("button", "erledigt"),
    ("button", "testbenachrichtigung"),
]

CARD_URL = f"/{DOMAIN}/muell-erinnerung.js"
