from datetime import timedelta

DOMAIN = "muell_erinnerung"
VERSION = "0.3.2"
PLATFORMS = ["sensor", "binary_sensor", "button"]

CONF_CALENDAR = "calendar_entity"
CONF_LOOKAHEAD = "lookahead_days"
CONF_CREATE_DEFAULTS = "create_default_types"
CONF_TIME = "reminder_time"
CONF_SNOOZE = "snooze_minutes"
CONF_NOTIFY = "notify_service"
CONF_DASHBOARD_URL = "dashboard_url"
CONF_PATTERN = "pattern"
CONF_ICON = "icon"

DEFAULT_LOOKAHEAD = 60
DEFAULT_TIME = "19:00:00"
DEFAULT_SNOOZE = 15
DEFAULT_DASHBOARD_URL = "/lovelace/0"
DEFAULT_ICON = "mdi:trash-can"
UPDATE_INTERVAL = timedelta(hours=1)

# Mülltypen sind Untereinträge (Subentries) des Config Entries.
SUBENTRY_TYPE = "waste_type"
DEFAULT_WASTE_TYPES = [
    {"name": "Biomüll", CONF_PATTERN: "bio", CONF_ICON: "mdi:leaf"},
    {"name": "Restmüll", CONF_PATTERN: "restmüll|restmuell|restabfall", CONF_ICON: "mdi:trash-can-outline"},
    {"name": "Papiermüll", CONF_PATTERN: "altpapier", CONF_ICON: "mdi:newspaper"},
    {"name": "Gelber Sack", CONF_PATTERN: "gelb", CONF_ICON: "mdi:sack-outline"},
]

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_state"

# Entity-IDs: <plattform>.muellerinnerung_<key>
ENTITY_PREFIX = "muellerinnerung"
DEVICE_NAME = "Müllerinnerung"
MAIN_ENTITIES = [
    ("sensor", "naechste_abholung"),
    ("binary_sensor", "aktiv"),
    ("button", "spaeter"),
    ("button", "erledigt"),
    ("button", "testbenachrichtigung"),
]

CARD_URL = f"/{DOMAIN}/muell-erinnerung.js"
