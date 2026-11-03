#!/usr/bin/env python3
import asyncio
import sys

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("read_token.py needs bleak: pip install bleak", file=sys.stderr)
    sys.exit(1)

TOKEN_SERVICE_UUID = "aa8fc844-22ec-431b-b565-4740da1f137a"
CLAIM_TOKEN_UUID = "bbbbbbbb-1234-5678-abcd-06050403ff01"
TIMEOUT = 20

NOT_FOUND = (
    "No secomat found. Press the WLAN button on the secomat briefly (it then lights up "
    "permanently), keep this computer next to the device and try again."
)


def is_secomat(device, advertisement) -> bool:
    name = advertisement.local_name or device.name or ""
    if name.upper().startswith("SECOMAT-"):
        return True
    return TOKEN_SERVICE_UUID in (uuid.lower() for uuid in advertisement.service_uuids)


async def main() -> None:
    print("Searching for the secomat via Bluetooth ...", file=sys.stderr)
    device = await BleakScanner.find_device_by_filter(is_secomat, timeout=TIMEOUT)
    if device is None:
        print(NOT_FOUND, file=sys.stderr)
        sys.exit(1)
    async with BleakClient(device, timeout=TIMEOUT) as client:
        token = await client.read_gatt_char(CLAIM_TOKEN_UUID)
    print(token.decode().strip("\x00").strip())


if __name__ == "__main__":
    asyncio.run(main())
