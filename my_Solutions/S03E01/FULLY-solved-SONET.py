
"""
Sensor anomaly detection - AI_DEVS evaluation task
Two-layer approach:
  1. Programmatic checks (fast, free)
  2. LLM checks for operator notes (batched + deduplicated)
"""

# COST:~ 0,5 USD!
# PROPOSED BY:
# LLM: claude sonnet 4

import json
import os
import re
import zipfile
import requests
from pathlib import Path
from collections import defaultdict
from anthropic import Anthropic

# ─── CONFIG ────────────────────────────────────────────────────────────────────
CENTRALA_API_KEY = os.environ.get("AI_DEV4_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
S03E01_SENSORS_DATA = os.environ.get("S03E01_SENSORS_DATA")

BASE_URL = os.environ["BASE_URL"]
VERIFICATION_ENDPOINT = os.environ["VERIFICATION_ENDPOINT"]

DATA_URL = S03E01_SENSORS_DATA
VERIFY_URL = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"
DATA_DIR = Path("claude/sensors")
ZIP_PATH = Path("claude/sensors.zip")

# ─── VALID RANGES per sensor field ────────────────────────────────────────────
RANGES = {
    "temperature_K":      (553, 873),
    "pressure_bar":       (60, 160),
    "water_level_meters": (5.0, 15.0),
    "voltage_supply_v":   (229.0, 231.0),
    "humidity_percent":   (40.0, 80.0),
}

# Which fields each sensor_type SHOULD measure (non-zero)
SENSOR_FIELDS = {
    "temperature":  {"temperature_K"},
    "pressure":     {"pressure_bar"},
    "water":        {"water_level_meters"},
    "voltage":      {"voltage_supply_v"},
    "humidity":     {"humidity_percent"},
}

ALL_FIELDS = set(RANGES.keys())

# ─── STEP 1: Download & extract ────────────────────────────────────────────────
def download_data():
    if DATA_DIR.exists() and any(DATA_DIR.iterdir()):
        print(f"[*] Data already present in {DATA_DIR}, skipping download.")
        return
    print("[*] Downloading sensors.zip ...")
    r = requests.get(DATA_URL, timeout=60)
    r.raise_for_status()
    ZIP_PATH.write_bytes(r.content)
    print(f"[*] Downloaded {len(r.content)//1024} KB. Extracting...")
    DATA_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(DATA_DIR)
    print(f"[*] Extracted to {DATA_DIR}")

# ─── STEP 2: Parse all JSON files ─────────────────────────────────────────────
def load_all(directory: Path) -> dict:
    records = {}
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records[path.stem] = data  # key = "0001", "0002", ...
        except Exception as e:
            print(f"  [!] Could not parse {path.name}: {e}")
    print(f"[*] Loaded {len(records)} records.")
    return records

# ─── STEP 3: Programmatic anomaly checks ──────────────────────────────────────
def get_active_fields(sensor_type: str) -> set:
    """Return the set of fields that should be non-zero for this sensor combo."""
    parts = [p.strip() for p in sensor_type.lower().split("/")]
    active = set()
    for part in parts:
        if part in SENSOR_FIELDS:
            active |= SENSOR_FIELDS[part]
        else:
            # Unknown sensor type — be conservative, flag separately
            active = None
            break
    return active

def check_programmatic(file_id: str, rec: dict) -> list[str]:
    """
    Returns list of anomaly reasons found purely by logic.
    Empty list = no programmatic anomaly.
    """
    anomalies = []
    sensor_type = rec.get("sensor_type", "")
    active = get_active_fields(sensor_type)

    for field, (lo, hi) in RANGES.items():
        val = rec.get(field, 0)
        if val is None:
            val = 0

        is_active = active is not None and field in active

        if is_active:
            # Field should have a real value — check range
            if not (lo <= val <= hi):
                anomalies.append(
                    f"{field}={val} out of range [{lo}, {hi}]"
                )
        else:
            # Field should be 0 (sensor doesn't measure it)
            if val != 0:
                anomalies.append(
                    f"{field}={val} should be 0 for sensor_type='{sensor_type}'"
                )

    return anomalies

# ─── STEP 4: LLM check on operator notes ──────────────────────────────────────
# Only for files where programmatic check found no anomaly — we need to verify
# whether the operator note matches the data.
# Also for anomalous files — operator might claim "all OK" while data is bad.

NOTE_SYSTEM_PROMPT = """You are a quality-control assistant for sensor data.
You receive batches of sensor readings. Each item has:
- file_id
- sensor_type
- field values (only active sensor fields, already range-validated by code)
- range_ok: true/false (did all active fields pass range check?)
- operator_notes: what the operator wrote

Your job: detect MISMATCHES between operator notes and reality:
  A) Operator says everything is OK / normal / stable, but range_ok=false
  B) Operator says there is an error / anomaly / problem, but range_ok=true

Rules:
- Ignore neutral/informational notes.
- Only flag clear contradictions.
- Respond ONLY with a JSON array of file_ids that have a mismatch. Example: ["0042","0137"]
- If no mismatches, respond: []
- No explanation, no markdown, just the JSON array.
"""

def build_llm_batch(file_ids: list, records: dict, prog_results: dict) -> str:
    """Build a compact text representation of a batch for the LLM."""
    items = []
    for fid in file_ids:
        rec = records[fid]
        sensor_type = rec.get("sensor_type", "")
        active = get_active_fields(sensor_type) or set()
        active_vals = {f: rec.get(f, 0) for f in active}
        range_ok = len(prog_results[fid]) == 0
        items.append({
            "file_id": fid,
            "sensor_type": sensor_type,
            "values": active_vals,
            "range_ok": range_ok,
            "operator_notes": rec.get("operator_notes", ""),
        })
    return json.dumps(items, ensure_ascii=False)

def check_notes_with_llm(
    file_ids: list,
    records: dict,
    prog_results: dict,
    client: Anthropic,
    batch_size: int = 200,
) -> set[str]:
    """
    Send batches to Claude, collect file_ids with note mismatches.
    Deduplication: group identical operator_notes to avoid redundant calls.
    """
    # --- deduplication: same note + same range_ok → same verdict
    note_key_to_ids = defaultdict(list)
    for fid in file_ids:
        note = records[fid].get("operator_notes", "").strip()
        range_ok = len(prog_results[fid]) == 0
        key = (note, range_ok)
        note_key_to_ids[key].append(fid)

    print(f"[*] Unique (note, range_ok) combos: {len(note_key_to_ids)} "
          f"(from {len(file_ids)} files)")

    # Pick one representative per unique key
    unique_ids = [ids[0] for ids in note_key_to_ids.values()]
    print(f"[*] Sending {len(unique_ids)} unique samples to LLM in batches of {batch_size}...")

    flagged_unique = set()
    for i in range(0, len(unique_ids), batch_size):
        batch = unique_ids[i : i + batch_size]
        payload = build_llm_batch(batch, records, prog_results)
        print(f"    batch {i//batch_size + 1}: {len(batch)} items...", end=" ", flush=True)

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=NOTE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": payload}],
        )
        raw = msg.content[0].text.strip()
        print(f"response: {raw[:120]}")
        try:
            flagged_batch = json.loads(raw)
            flagged_unique.update(flagged_batch)
        except json.JSONDecodeError:
            # Try to extract array from response
            m = re.search(r'\[.*?\]', raw, re.DOTALL)
            if m:
                flagged_unique.update(json.loads(m.group()))

    # Expand back: if representative was flagged, flag ALL ids with same key
    result = set()
    for fid in flagged_unique:
        rec = records.get(fid)
        if not rec:
            continue
        note = rec.get("operator_notes", "").strip()
        range_ok = len(prog_results[fid]) == 0
        key = (note, range_ok)
        for sibling in note_key_to_ids[key]:
            result.add(sibling)

    return result

# ─── STEP 5: Send answer ───────────────────────────────────────────────────────
def send_answer(anomalous_ids: list, api_key: str):
    payload = {
        "apikey": api_key,
        "task": "evaluation",
        "answer": {"recheck": sorted(anomalous_ids)},
    }
    print(f"\n[*] Sending {len(anomalous_ids)} anomalous IDs to Centrala...")
    r = requests.post(VERIFY_URL, json=payload, timeout=30)
    print(f"[*] Response [{r.status_code}]: {r.text[:500]}")

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    download_data()
    records = load_all(DATA_DIR)

    # --- Programmatic pass
    prog_results = {}   # file_id -> list of anomaly strings
    for fid, rec in records.items():
        prog_results[fid] = check_programmatic(fid, rec)

    prog_anomalies = {fid for fid, reasons in prog_results.items() if reasons}
    print(f"\n[*] Programmatic anomalies found: {len(prog_anomalies)}")

    print(prog_anomalies)

        

    # --- LLM pass (operator notes check)
    if not ANTHROPIC_API_KEY:
        print("\n[!] No ANTHROPIC_API_KEY set — skipping LLM note check.")
        note_anomalies = set()
    else:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        # Send ALL files to LLM (it needs to check notes for both good and bad data)
        note_anomalies = check_notes_with_llm(
            list(records.keys()), records, prog_results, client, batch_size=200
        )
        print(f"\n[*] LLM note anomalies found: {len(note_anomalies)}")

    # --- Merge results
    all_anomalies = sorted(prog_anomalies | note_anomalies)
    print(all_anomalies)
    print(f"\n[*] TOTAL anomalous files: {len(all_anomalies)}")

    # --- Send to Centrala
    if CENTRALA_API_KEY and CENTRALA_API_KEY != "YOUR_CENTRALA_KEY":
        send_answer(all_anomalies, CENTRALA_API_KEY)
    else:
        print("[!] Set CENTRALA_KEY env var to send the answer.")
        print("Preview:", json.dumps(all_anomalies))

if __name__ == "__main__":
    main()
