# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Home Assistant Custom Integration** for Krüger Secomat dehumidifiers. The integration communicates with Secomat devices through the Krüger Cloud API at `seco.krueger.ch:8080`.

**Authentication**: Uses a `claim-token` header obtained by intercepting the official Secomat mobile app traffic with mitmproxy.

**Architecture**: Cloud polling integration (IoT class: `cloud_polling`) with a 30-second update interval.

## Core Architecture

### Component Flow
1. **Config Flow** (`config_flow.py`) → Validates claim token and sets up entry
2. **Integration Setup** (`__init__.py`) → Creates API client and coordinator
3. **Coordinator** (`coordinator.py`) → Manages polling and data updates
4. **Platform Entities** (`sensor.py`, `switch.py`, `select.py`) → Expose device state to HA

### Key Components

**API Client** (`api.py`):
- `SecomatAPI` class handles all HTTP communication with Krüger Cloud
- Manages aiohttp session lifecycle (creates own session if not provided)
- All methods are async and use 10-second timeouts
- Custom exception: `SecomatAPIError` for all API failures

**Coordinator** (`coordinator.py`):
- `SecomatCoordinator` extends `DataUpdateCoordinator`
- Polls `api.get_state()` every 30 seconds (configurable in `const.py`)
- Returns dict with device state (temperature, humidity, mode, etc.)
- Converts `SecomatAPIError` to `UpdateFailed` for HA error handling

**Platforms**:
- **Sensors**: Temperature, Humidity, State, Operating Mode, Firmware
- **Switches**: Laundry Drying, Room Drying
- **Select**: Target Moisture Level (wet/dry/extra_dry)

All entity classes inherit from `CoordinatorEntity` for automatic updates.

## API Commands

Available commands sent via `api.send_command(command, args)`:

| Command | Args | Description |
|---------|------|-------------|
| `OFF` | None | Turn off device |
| `PRG_WASH_AUTO` | None | Start laundry drying (auto) |
| `PRG_WASH_TIMER` | None | Start laundry drying (timer) |
| `PRG_ROOM_ON` | None | Enable room drying |
| `PRG_ROOM_OFF` | None | Disable room drying |
| `SET_TARGET_HUMIDITY` | `{"level": 0-2}` | Set target moisture level |

## State Mappings

Defined in `const.py`:

**Secomat States** (`secomat_state`):
- 0=off, 1=standby, 2=running, 3=drying, 4=cooling, 5=pause, 6=ready

**Operating Modes** (`operating_mode`):
- 0=off, 1=laundry_drying, 2=room_drying, 3=ventilation

**Humidity Levels** (`target_humidity_level`):
- 0=wet, 1=dry, 2=extra_dry

## Development Commands

### Testing the Integration
```bash
# Home Assistant uses pytest for testing (not implemented in this repo yet)
pytest tests/
```

### Local Installation
```bash
# Copy to HA config directory
cp -r custom_components/secomat /path/to/homeassistant/config/custom_components/

# Restart Home Assistant
# Use HA UI or CLI depending on installation method
```

### Debugging
- Enable debug logging in HA `configuration.yaml`:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.secomat: debug
  ```
- Check logs: `~/.homeassistant/home-assistant.log` or via HA UI

## Code Patterns

### Adding New API Commands
1. Add command constant to `const.py`
2. Add method to `SecomatAPI` class in `api.py`
3. Use in platform entity (sensor/switch/select)

### Adding New Entities
1. Create sensor/switch/select class inheriting from `SecomatBaseSensor`/`SecomatBaseSwitch`/etc
2. Set `_attr_unique_id` as `f"{serial}_{entity_type}"`
3. Implement required properties (`native_value`, `is_on`, etc.)
4. Add to entity list in platform's `async_setup_entry()`

### Session Management
- API client manages its own aiohttp session if none provided
- **Important**: Always call `api.close()` in cleanup paths (`config_flow.py`, `__init__.py`)
- Coordinator automatically closes API session via `async_unload_entry()`

## API Response Format

GET request returns:
```json
{
  "type": "STATE",
  "payload": {
    "ambient_temperature": 20.87,
    "humidity": 50.50,
    "secomat_state": 6,
    "operating_mode": 0,
    "room_drying_enabled": 0,
    "target_humidity_level": 1,
    "serial_number": "43.16554",
    "fw_version": "0.3.06"
  }
}
```

POST command returns:
```json
{
  "status": "OK"
}
```

## Important Notes

- **No local device communication**: Device has no open ports, all communication goes through Krüger Cloud
- **Token security**: Claim token is stored in HA config entry (encrypted at rest)
- **Entity naming**: Uses `has_entity_name = True` pattern (HA 2022.9+)
- **Unique ID format**: `{serial_number}_{entity_type}` prevents duplicate entities
- **Device info**: Shared across all entities via identical `device_info` dict
