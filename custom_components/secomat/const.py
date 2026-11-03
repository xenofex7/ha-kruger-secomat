DOMAIN = "secomat"

CONF_CLAIM_TOKEN = "claim_token"

API_BASE_URL = "https://seco.krueger.ch:8080/app1/v1/plc"

DEFAULT_SCAN_INTERVAL = 60

SECOMAT_STATES = {
    0: "ready",
    **{state: "drying" for state in range(1, 15)},
    15: "finished",
    16: "aborted",
    19: "error",
}

OPERATING_MODES = {
    0: "standby",
    1: "no_program",
    2: "laundry_program",
}

CMD_OFF = "OFF"
CMD_WASH_AUTO = "PRG_WASH_AUTO"
CMD_WASH_MANUAL_ON = "PRG_WASH_MANUAL_ON"
CMD_ROOM_ON = "PRG_ROOM_ON"
CMD_ROOM_OFF = "PRG_ROOM_OFF"
CMD_PARAMETER_CHANGE = "PARAMETER_CHANGE"

SERVICE_START_DRYING = "start_drying"

HUMIDITY_LEVELS = {
    0: "very_dry",
    1: "dry",
    2: "medium",
    3: "moist",
}
