# 🌡️ Krüger Secomat - Home Assistant Integration

Custom integration for [Krüger Secomat](https://www.krueger.ch/secomat/) dehumidifiers.

## What I did
1. **Found Secomat on the network** → ESP32-based (Espressif), no open ports
2. **Intercepted app traffic** with mitmproxy → found Cloud API
3. **Reverse-engineered the API** → `seco.krueger.ch:8080`
4. **Built HA Custom Integration** → Sensors + Switches

## API Overview

|  | Description |
|---|---|
| **Endpoint** | `https://seco.krueger.ch:8080/app1/v1/plc` |
| **Auth** | Header: `claim-token: <your-token>` |
| **Status** | `GET` → JSON with temp, humidity, state |
| **Control** | `POST` with `{"command":"...","args":{}}` |

### Commands (verified)
| Command | Description |
|---------|-------------|
| `OFF` | Turn off |
| `PRG_WASH_AUTO` | Laundry drying (auto) |
| `PRG_WASH_TIMER` | Laundry drying (timer) |
| `PRG_ROOM_ON` | Room drying on |
| `PRG_ROOM_OFF` | Room drying off |

### Commands (unknown, not reverse-engineered yet)
- Set target humidity level (slider in the app)
- Toggle target-humidity lock (lock icon)
- Toggle HMI backlight ("Control Lights" button)

### Status Fields
| Field | Example | Description |
|-------|---------|-------------|
| `ambient_temperature` | 20.87 | Temperature °C |
| `humidity` | 50.50 | Humidity % |
| `secomat_state` | 0=ready, 2=starting, 6=drying, 15=drying_high | Runtime phase |
| `operating_mode` | 0=standby, 1=no_program, 2=laundry_program | Program state |
| `room_drying_enabled` | 0/1 | Room drying active |
| `target_humidity_level` | 0=very_dry, 1=dry, 2=medium, 3=moist | Target moisture |
| `target_humidity_level_locked` | 0/1 | Lock on target moisture slider |
| `hmi_backlight` | 0/1 | Device display backlight |
| `eye_seeing_object` | 0/1 | Proximity/laundry detection sensor |
| `next_start` | ISO timestamp or 0 | Scheduled start (0 = none) |
| `error_list` | [] | Active errors |
| `serial_number` | 43.16554 | Serial number |
| `fw_version` | 0.3.06 | Firmware version |

## Features

**Sensors:**
- Temperature
- Humidity
- State (ready / starting / drying / drying_high)
- Operating Mode (standby / no_program / laundry_program)
- Target Moisture (very_dry / dry / medium / moist — read-only)
- Next Start (timestamp, diagnostic)
- Error Count (diagnostic, with list attribute)
- Firmware (diagnostic)
- Device Tick (diagnostic, disabled by default)

**Binary sensors:**
- Eye Detects Object (proximity)
- Display Backlight (diagnostic)
- Problem (on when `error_list` is non-empty, diagnostic)

**Switches:**
- Laundry Drying (on/off)
- Room Drying (on/off)

## Installation

### HACS (recommended)
1. Add this repository as a custom repository in HACS
2. Install "Krüger Secomat"
3. Restart Home Assistant

### Manual
1. Copy `custom_components/secomat/` to your HA `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **"Krüger Secomat"**
3. Enter your **Claim Token**

## How to get the Claim Token

The claim token authenticates your requests to the Secomat Cloud API. To obtain it:

1. Install `mitmproxy` on a computer in your local network
   ```bash
   sudo apt install mitmproxy
   ```
2. Start mitmproxy with increased file limits:
   ```bash
   sudo bash -c 'ulimit -n 65536 && mitmdump --listen-port 8888 --ssl-insecure'
   ```
3. On your phone (iPhone/Android):
   - Go to **WiFi Settings → Proxy → Manual**
   - Server: `<your-computer-ip>`, Port: `8888`
4. Open browser → go to `http://mitm.it` → install & trust the CA certificate
   - **iOS**: Settings → General → About → Certificate Trust Settings → enable mitmproxy
5. Open the **Secomat app** and interact with it
6. In the mitmproxy log, look for requests to `seco.krueger.ch:8080`
7. The `claim-token` header value is your token
8. **Disable the proxy** on your phone when done!

## File Structure

```
custom_components/secomat/
├── __init__.py          # Integration setup
├── api.py               # Secomat Cloud API client
├── config_flow.py       # Setup dialog
├── const.py             # Constants & mappings
├── coordinator.py       # Data update coordinator
├── manifest.json        # HA integration manifest
├── sensor.py            # All sensors (temp, humidity, state, target moisture)
├── strings.json         # UI strings
├── switch.py            # Laundry/room drying switches
└── translations/
    └── en.json          # English translations
```

## Technical Details

- **Device**: ESP32 (Espressif) with WiFi
- **Communication**: Device ↔ Krüger Cloud ↔ App/HA
- **Polling interval**: 30 seconds (configurable in `const.py`)
- **IoT Class**: Cloud Polling

## Credits

API reverse-engineered with mitmproxy, February 2026.

## License

MIT
