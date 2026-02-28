#!/usr/bin/env python3
"""
Secomat API Test Suite
======================
Unified test script for the Krüger Secomat integration.
Can be run standalone without Home Assistant.

Usage:
  python3 test.py <claim-token>           # Run basic tests
  python3 test.py <claim-token> -i        # Interactive mode
  python3 test.py <claim-token> --all     # Test all command variations
"""
import asyncio
import sys
import aiohttp
from typing import Any


# ============================================================================
# Standalone API Client (no Home Assistant dependencies)
# ============================================================================

API_BASE_URL = "https://seco.krueger.ch:8080/app1/v1/plc"


class SecomatAPIError(Exception):
    """Secomat API error."""


class SecomatAPI:
    """Krüger Secomat API client (standalone version)."""

    def __init__(self, claim_token: str, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize the API client."""
        self._claim_token = claim_token
        self._session = session
        self._own_session = session is None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    @property
    def _headers(self) -> dict[str, str]:
        """Return API headers."""
        return {
            "claim-token": self._claim_token,
            "api": "1",
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Secomat/1.0.3 HA-Integration",
        }

    async def get_state(self) -> dict[str, Any]:
        """Get current Secomat state."""
        session = await self._ensure_session()
        try:
            async with session.get(
                API_BASE_URL,
                headers=self._headers,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise SecomatAPIError(f"API returned {response.status}")
                data = await response.json()
                if data.get("type") == "STATE":
                    return data.get("payload", {})
                return data
        except aiohttp.ClientError as err:
            raise SecomatAPIError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise SecomatAPIError("Request timeout") from err

    async def send_command(self, command: str, args: dict | None = None) -> bool:
        """Send a command to the Secomat."""
        session = await self._ensure_session()
        payload = {"command": command, "args": args or {}}
        try:
            async with session.post(
                API_BASE_URL,
                headers=self._headers,
                json=payload,
                ssl=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise SecomatAPIError(f"API returned {response.status}")
                data = await response.json()
                return data.get("status") == "OK"
        except aiohttp.ClientError as err:
            raise SecomatAPIError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise SecomatAPIError("Request timeout") from err

    async def close(self) -> None:
        """Close the session."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()


# ============================================================================
# Basic Tests
# ============================================================================

async def test_get_state(api):
    """Test getting current device state."""
    print("\n=== Testing GET State ===")
    try:
        state = await api.get_state()
        print("✅ Success! Current state:")
        for key, value in state.items():
            print(f"  {key}: {value}")
        return state
    except SecomatAPIError as err:
        print(f"❌ Error: {err}")
        return None


async def test_command(api, command, args=None):
    """Test sending a command to the device."""
    args_str = f" with args {args}" if args else ""
    print(f"\n=== Testing Command: {command}{args_str} ===")
    try:
        result = await api.send_command(command, args)
        if result:
            print(f"✅ Success! Command '{command}' executed")
        else:
            print(f"⚠️  Command sent but status was not 'OK'")
        return True
    except SecomatAPIError as err:
        print(f"❌ Error: {err}")
        return False


async def run_basic_tests(claim_token):
    """Run basic API tests."""
    print(f"🔧 Testing Secomat API with token: {claim_token[:10]}...")

    api = SecomatAPI(claim_token)

    try:
        # Get current state
        state = await test_get_state(api)
        if not state:
            print("\n❌ Cannot proceed without valid state")
            return

        # Show important values
        print("\n📊 Key Values:")
        print(f"  Temperature: {state.get('ambient_temperature')}°C")
        print(f"  Humidity: {state.get('humidity')}%")
        print(f"  State: {state.get('secomat_state')}")
        print(f"  Operating Mode: {state.get('operating_mode')}")
        print(f"  Target Humidity Level: {state.get('target_humidity_level')}")

        # Test safe commands (uncomment to test device state changes)
        print("\n⚠️  Device state change commands are commented out")
        print("Uncomment lines in test.py to test:")
        print("  - OFF")
        print("  - PRG_WASH_AUTO")
        print("  - PRG_ROOM_ON")
        print("  - SET_TARGET_HUMIDITY")

        # await test_command(api, "OFF")
        # await asyncio.sleep(2)
        # await test_command(api, "PRG_WASH_AUTO")

    finally:
        await api.close()
        print("\n✅ Tests completed, API client closed")


# ============================================================================
# Interactive Mode
# ============================================================================

async def run_interactive(claim_token):
    """Interactive command testing mode."""
    print(f"🔧 Interactive Mode - Token: {claim_token[:10]}...")

    api = SecomatAPI(claim_token)

    try:
        # Get current state
        state = await api.get_state()
        print("\n📊 Current state:")
        print(f"  target_humidity_level: {state.get('target_humidity_level')}")
        print(f"  humidity: {state.get('humidity')}%")
        print(f"  secomat_state: {state.get('secomat_state')}")

        print("\n" + "="*60)
        print("Interactive Command Tester")
        print("="*60)
        print("\nEnter command to test (or 'quit' to exit)")
        print("Format: COMMAND_NAME arg1=value1 arg2=value2")
        print("\nExamples:")
        print("  OFF")
        print("  PRG_WASH_AUTO")
        print("  SET_TARGET_HUMIDITY level=2")
        print("  PRG_ROOM_ON")
        print()

        while True:
            user_input = input("> ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                continue

            # Parse input
            parts = user_input.split()
            command = parts[0]
            args = {}

            for part in parts[1:]:
                if '=' in part:
                    key, value = part.split('=', 1)
                    # Try to convert to int
                    try:
                        args[key] = int(value)
                    except ValueError:
                        args[key] = value

            # Send command
            print(f"Sending: {command} with {args if args else 'no args'}")
            try:
                result = await api.send_command(command, args if args else None)
                if result:
                    print("✅ Success!")
                else:
                    print("⚠️  Command sent but response was not OK")

                # Show new state
                await asyncio.sleep(1)
                new_state = await api.get_state()
                print(f"New state: secomat_state={new_state.get('secomat_state')}, "
                      f"target_humidity_level={new_state.get('target_humidity_level')}")

            except Exception as err:
                print(f"❌ Error: {err}")

    finally:
        await api.close()
        print("\n✅ Interactive mode closed")


# ============================================================================
# Comprehensive Command Testing
# ============================================================================

async def test_raw_command(session, headers, command, args=None):
    """Test a single command using raw HTTP."""
    API_BASE_URL = "https://seco.krueger.ch:8080/app1/v1/plc"
    payload = {"command": command, "args": args or {}}

    try:
        async with session.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            ssl=True,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            result = await response.json()

            if response.status == 200:
                print(f"✅ {command:30} {str(args):40} -> {result}")
                return True
            else:
                print(f"❌ {command:30} {str(args):40} -> Status {response.status}")
                return False
    except Exception as err:
        print(f"⚠️  {command:30} {str(args):40} -> Error: {err}")
        return False


async def run_all_tests(claim_token):
    """Test all possible command variations (for development)."""
    print(f"🔧 Testing ALL command variations - Token: {claim_token[:10]}...")

    headers = {
        "claim-token": claim_token,
        "api": "1",
        "accept": "*/*",
        "content-type": "application/json",
        "user-agent": "Secomat/1.0.3 HA-Integration",
    }

    API_BASE_URL = "https://seco.krueger.ch:8080/app1/v1/plc"

    async with aiohttp.ClientSession() as session:
        # Get current state
        async with session.get(API_BASE_URL, headers=headers, ssl=True) as response:
            data = await response.json()
            state = data.get("payload", {})
            print(f"\nCurrent: secomat_state={state.get('secomat_state')}, "
                  f"target_humidity_level={state.get('target_humidity_level')}")
            print()

        print("="*80)
        print("Testing command variations with different prefixes and arg names...")
        print("="*80)
        print()

        # Test various command/arg combinations
        prefixes = ["", "CMD_", "PRG_", "SET_"]
        bases = ["TARGET_HUMIDITY", "HUMIDITY_LEVEL", "HUMIDITY", "MOISTURE"]

        for prefix in prefixes:
            for base in bases:
                cmd = f"{prefix}{base}"
                await test_raw_command(session, headers, cmd, {"level": 2})
                await asyncio.sleep(0.2)

        print("\nTesting different argument names...")
        arg_variations = [
            {"level": 2},
            {"value": 2},
            {"target_humidity_level": 2},
            {"humidity_level": 2},
        ]

        for args in arg_variations:
            await test_raw_command(session, headers, "SET_TARGET_HUMIDITY", args)
            await asyncio.sleep(0.2)


# ============================================================================
# Main Entry Point
# ============================================================================

def print_usage():
    """Print usage information."""
    print(__doc__)
    print("\nAvailable modes:")
    print("  (default)  Run basic API tests")
    print("  -i         Interactive command testing")
    print("  --all      Test all possible command variations")
    print("\nExamples:")
    print("  python3 test.py abc123def456")
    print("  python3 test.py abc123def456 -i")
    print("  python3 test.py abc123def456 --all")


async def main():
    """Main test function."""
    # Parse arguments
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)

    claim_token = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else None

    if not claim_token or claim_token.startswith('-'):
        print("❌ No claim token provided!")
        print_usage()
        sys.exit(1)

    # Run appropriate test mode
    if mode == '-i' or mode == '--interactive':
        await run_interactive(claim_token)
    elif mode == '--all':
        await run_all_tests(claim_token)
    else:
        await run_basic_tests(claim_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
