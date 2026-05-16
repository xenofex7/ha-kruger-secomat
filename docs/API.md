# Krüger Secomat Cloud API Reference

Reverse-engineered notes on the Krüger Cloud API that this integration talks to. Useful if you want to script against the device directly, build another client, or extend the integration with new commands.

## Endpoint

| | Description |
|---|---|
| URL | `https://seco.krueger.ch:8080/app1/v1/plc` |
| Auth | `claim-token: <your-token>` header (see [Obtaining the claim token](../README.md#obtaining-the-claim-token)) |
| Status | `GET` returns the current device state as JSON |
| Control | `POST` with `{"command": "<name>", "args": {...}}` |

The device itself has no open ports - all communication runs through the Krüger Cloud.

## Commands

### Verified

| Command | Args | Description |
|---------|------|-------------|
| `OFF` | none | Turn the device off |
| `PRG_WASH_AUTO` | none | Start laundry drying (auto mode) |
| `PRG_WASH_MANUAL_ON` | `{"prg_wash_starttime": <delay_seconds>}` | Start laundry drying (manual mode); value is seconds from now until start (0 = immediate). Verified on hardware. |
| `PRG_WASH_MANUAL_OFF` | none | Cancel a pending delayed manual start without turning the device off. Verified on hardware. |
| `PRG_WASH_TIMER` | none | Start laundry drying (timer mode) |
| `PRG_ROOM_ON` | none | Enable room drying |
| `PRG_ROOM_OFF` | none | Disable room drying |
| `PARAMETER_CHANGE` | `{"residual_moisture_target": 0..3}` | Set the target moisture level. Discovered by [@ratsch](https://github.com/ratsch/ha-kruger-secomat). |
| `PARAMETER_CHANGE` | `{"lock_residual_moisture_target": 0\|1}` | Lock or unlock the moisture target. The device accepts changes to `residual_moisture_target` even when locked - the lock is enforced only by the official app. Discovered by [@ratsch](https://github.com/ratsch/ha-kruger-secomat). |

### Known but not reverse-engineered

- Toggle HMI backlight ("Control Lights" button in the app)

## Status fields

`GET` returns:

```json
{
  "type": "STATE",
  "payload": {
    "now": 13256016,
    "secomat_state": 6,
    "operating_mode": 2,
    "room_drying_enabled": 1,
    "ambient_temperature": 20.87,
    "humidity": 50.50,
    "next_start": 0,
    "target_humidity_level": 1,
    "target_humidity_level_locked": 1,
    "hmi_backlight": 0,
    "eye_seeing_object": 1,
    "error_list": [],
    "fw_version": "0.3.06",
    "serial_number": "43.16554"
  }
}
```

| Field | Example | Description |
|-------|---------|-------------|
| `ambient_temperature` | `20.87` | Temperature in °C |
| `humidity` | `50.50` | Relative humidity in % |
| `secomat_state` | `0` = ready, `2` = starting, `6` = drying, `15` = drying_high | Runtime phase (gaps remain - other values appear during transitions) |
| `operating_mode` | `0` = standby, `1` = no_program, `2` = laundry_program | Program state |
| `room_drying_enabled` | `0` / `1` | Room drying active |
| `target_humidity_level` | `0` = very_dry, `1` = dry, `2` = medium, `3` = moist | Target moisture level |
| `target_humidity_level_locked` | `0` / `1` | Lock on the moisture target (app-enforced only, see above) |
| `hmi_backlight` | `0` / `1` | Device display backlight |
| `eye_seeing_object` | `0` / `1` | Proximity / laundry detection sensor |
| `next_start` | ISO timestamp or `0` | Scheduled start time, `0` means no pending start |
| `error_list` | `[]` | Active error codes |
| `serial_number` | `"43.16554"` | Device serial number |
| `fw_version` | `"0.3.06"` | Firmware version |
| `now` | `13256016` | Device uptime in deciseconds (rough estimate) |

## Command response

`POST` returns:

```json
{
  "status": "OK"
}
```

Non-OK status or HTTP error codes indicate a malformed command, an unknown command, or an authentication failure.

## Notes

- The integration polls `GET` every 30 seconds.
- All `POST` commands are fire-and-forget; the integration triggers a state refresh after each successful command to pick up the new state.
- Timeouts are set to 10 seconds per request.
