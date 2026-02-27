"""Constants for the Krüger Secomat integration."""

DOMAIN = "secomat"

CONF_CLAIM_TOKEN = "claim_token"
CONF_SERIAL = "serial_number"

API_BASE_URL = "https://seco.krueger.ch:8080/app1/v1/plc"

# Polling interval in seconds
DEFAULT_SCAN_INTERVAL = 30

# Secomat states
SECOMAT_STATES = {
    0: "off",
    1: "standby",
    2: "running",
    3: "drying",
    4: "cooling",
    5: "pause",
    6: "ready",
}

# Operating modes
OPERATING_MODES = {
    0: "off",
    1: "laundry_drying",
    2: "room_drying",
    3: "ventilation",
}

# Commands
CMD_OFF = "OFF"
CMD_WASH_AUTO = "PRG_WASH_AUTO"
CMD_WASH_TIMER = "PRG_WASH_TIMER"
CMD_ROOM_ON = "PRG_ROOM_ON"
CMD_ROOM_OFF = "PRG_ROOM_OFF"

# Target humidity levels
HUMIDITY_LEVELS = {
    0: "wet",
    1: "dry",
    2: "extra_dry",
}
