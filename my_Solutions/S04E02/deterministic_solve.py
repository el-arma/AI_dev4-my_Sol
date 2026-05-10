"""
ALTERNATIVE - DETERMINISTIC SOLUTION - NO AI
WORKS: 1/3

S04E02 - Wind Power Scheduler
Deterministic async solution, no LLM overhead.

Flow:
1. start  (sync)
2. [parallel] get documentation (sync direct), queue weather / turbinecheck / powerplantcheck
3. Single polling loop:
   - On weather → compute config points, immediately queue unlockCodeGenerator for each
   - Collect turbinecheck + powerplantcheck  (required before done)
   - Collect all unlock codes
4. Send bulk config
5. done
"""

import asyncio
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY: str = os.environ["AI_DEV4_API_KEY"]
BASE_URL: str = os.environ["BASE_URL"]
VERIFY_EP: str = os.environ["VERIFICATION_ENDPOINT"]
VERIFY_URL: str = f"{BASE_URL}/{VERIFY_EP}"
TASK: str = "windpower"


# Low-level API helper

async def api(client: httpx.AsyncClient, answer: dict[str, Any]) -> dict[str, Any]:
    payload = {"apikey": API_KEY, "task": TASK, "answer": answer}
    r = await client.post(VERIFY_URL, json=payload)
    r.raise_for_status()
    return r.json()


# Weather analysis

def analyze_weather(
    forecast: list[dict],
    cutoff_ms: float,
    min_op_ms: float,
) -> list[dict]:
    """
    Return list of config points:
      - ALL slots where windMs > cutoff  → pitch=90, mode=idle   (storm protection)
      - ONE best slot where windMs in [min_op_ms, cutoff] → pitch=0, mode=production
        Best = highest windMs (maximises energy output).
    """
    storm_points: list[dict] = []
    best_prod: dict | None = None
    best_wind: float = -1.0

    for entry in forecast:
        ts: str = entry["timestamp"]       # "2026-05-04 18:00:00"
        wind: float = entry["windMs"]
        date_str, time_str = ts.split(" ")
        hour_str = time_str                 # keep "HH:00:00" as-is

        if wind > cutoff_ms:
            storm_points.append({
                "date": date_str,
                "hour": hour_str,
                "windMs": wind,
                "pitchAngle": 90,
                "mode": "idle",
            })
        elif wind >= min_op_ms and wind > best_wind:
            best_wind = wind
            best_prod = {
                "date": date_str,
                "hour": hour_str,
                "windMs": wind,
                "pitchAngle": 0,
                "mode": "production",
            }

    result = list(storm_points)
    if best_prod:
        result.append(best_prod)

    return result

async def solve() -> None:
    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:

        t0 = time.monotonic()

        # Step 1: start 
        start_resp = await api(client, {"action": "start"})
        print(f"[{time.monotonic()-t0:.1f}s] start → {start_resp}")

        # Step 2: parallel – documentation (sync) + queue 3 async ──
        doc_resp, *_ = await asyncio.gather(
            api(client, {"action": "get", "param": "documentation"}),
            api(client, {"action": "get", "param": "weather"}),
            api(client, {"action": "get", "param": "turbinecheck"}),
            api(client, {"action": "get", "param": "powerplantcheck"}),
        )
        print(f"[{time.monotonic()-t0:.1f}s] documentation received, 3 async queued")

        cutoff_ms: float = doc_resp["safety"]["cutoffWindMs"]
        min_op_ms: float = doc_resp["safety"]["minOperationalWindMs"]
        print(f"  cutoff={cutoff_ms} m/s  min_op={min_op_ms} m/s")

        # Step 3 / 5 combined: single polling loop 
        collected: dict[str, dict] = {}          # weather / turbinecheck / powerplantcheck
        config_points: list[dict] = []
        unlock_codes: dict[str, str] = {}        # "date hour" → unlockCode
        unlock_remaining: int | None = None       # None until unlock codes queued
        unlock_queued: bool = False

        NEEDED_INITIAL = {"weather", "turbinecheck", "powerplantcheck"}

        while True:
            elapsed = time.monotonic() - t0

            # Safety guard: abort if dangerously close to 40s
            if elapsed > 38:
                print(f"[{elapsed:.1f}s] WARNING: approaching timeout, aborting poll")
                break

            resp = await api(client, {"action": "getResult"})
            src = resp.get("sourceFunction")
            code = resp.get("code", -1)

            # Queue empty → wait briefly and retry
            if code == 11 or src is None:
                await asyncio.sleep(0.15)
                continue

            print(f"[{time.monotonic()-t0:.1f}s] received sourceFunction={src}")

            # Initial data 
            if src == "weather" and "weather" not in collected:
                collected["weather"] = resp
                config_points = analyze_weather(
                    resp["forecast"], cutoff_ms, min_op_ms
                )
                print(f"  config_points: {[(p['date'], p['hour'], p['windMs'], p['mode']) for p in config_points]}")

                # Queue unlock codes immediately (parallel burst)
                if config_points and not unlock_queued:
                    unlock_queued = True
                    await asyncio.gather(*[
                        api(client, {
                            "action": "unlockCodeGenerator",
                            "startDate": p["date"],
                            "startHour": p["hour"],
                            "windMs": p["windMs"],
                            "pitchAngle": p["pitchAngle"],
                        })
                        for p in config_points
                    ])
                    unlock_remaining = len(config_points)
                    print(f"[{time.monotonic()-t0:.1f}s] queued {unlock_remaining} unlockCodeGenerator(s)")

            elif src in ("turbinecheck", "powerplantcheck") and src not in collected:
                collected[src] = resp

            elif src == "unlockCodeGenerator" and unlock_remaining is not None:
                sp = resp.get("signedParams", {})
                key = f"{sp['startDate']} {sp['startHour']}"
                unlock_codes[key] = resp["unlockCode"]
                unlock_remaining -= 1
                print(f"[{time.monotonic()-t0:.1f}s] unlock code for {key} → remaining={unlock_remaining}")

            # Exit condition 
            initial_done = NEEDED_INITIAL <= set(collected)
            unlocks_done = unlock_remaining is not None and unlock_remaining == 0
            if initial_done and unlocks_done:
                break

        # Step 7: build + send bulk config 
        configs: dict[str, dict] = {}
        for p in config_points:
            key = f"{p['date']} {p['hour']}"
            if key not in unlock_codes:
                print(f"  WARNING: missing unlock code for {key}, skipping")
                continue
            configs[key] = {
                "pitchAngle": p["pitchAngle"],
                "turbineMode": p["mode"],
                "unlockCode": unlock_codes[key],
            }

        config_resp = await api(client, {"action": "config", "configs": configs})
        print(f"[{time.monotonic()-t0:.1f}s] config → {config_resp}")

        # Step 8: do
        done_resp = await api(client, {"action": "done"})
        print(f"[{time.monotonic()-t0:.1f}s] done → {done_resp}")

        if "FLG:" in str(done_resp):
            import hashlib
            msg = done_resp.get("message", "")
            flag = msg.split("{FLG:")[1].split("}")[0]
            sha = hashlib.sha256(flag.encode()).hexdigest()
            print(f"\n🚩 FLAG: {flag}\nSHA256: {sha}")


if __name__ == "__main__":
    asyncio.run(solve())
