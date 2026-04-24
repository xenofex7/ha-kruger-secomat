#!/usr/bin/env python3
"""Live-watcher for Secomat state. Polls every 2s, prints on change."""
import asyncio
import sys
from datetime import datetime

import aiohttp

API = "https://seco.krueger.ch:8080/app1/v1/plc"
WATCH_FIELDS = [
    "secomat_state",
    "operating_mode",
    "room_drying_enabled",
    "target_humidity_level",
    "target_humidity_level_locked",
    "eye_seeing_object",
    "hmi_backlight",
    "next_start",
    "error_list",
]


async def main(token: str) -> None:
    headers = {
        "claim-token": token,
        "api": "1",
        "accept": "*/*",
        "content-type": "application/json",
        "user-agent": "Secomat/1.0.3 HA-Integration",
    }
    prev: dict = {}
    async with aiohttp.ClientSession() as session:
        print("Watching Secomat — change modes in the app, I print diffs only.")
        print(f"Fields: {', '.join(WATCH_FIELDS)}\n")
        while True:
            try:
                async with session.get(
                    API,
                    headers=headers,
                    ssl=True,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    data = (await r.json()).get("payload", {})
            except Exception as e:
                print(f"[{datetime.now():%H:%M:%S}] error: {e}")
                await asyncio.sleep(2)
                continue

            snap = {k: data.get(k) for k in WATCH_FIELDS}
            if snap != prev:
                ts = f"{datetime.now():%H:%M:%S}"
                if not prev:
                    print(f"[{ts}] INITIAL: {snap}")
                else:
                    diff = {k: (prev.get(k), snap[k]) for k in snap if snap[k] != prev.get(k)}
                    pretty = ", ".join(f"{k}: {a}→{b}" for k, (a, b) in diff.items())
                    print(f"[{ts}] {pretty}")
                prev = snap
            await asyncio.sleep(2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: watch.py <token>")
        sys.exit(1)
    try:
        asyncio.run(main(sys.argv[1]))
    except KeyboardInterrupt:
        print("\nstopped.")
