# DDA
# DETERMINISTIC ANOMALY DETECTOR

import json
from pathlib import Path

# Parse all JSON files
def load_sensors_data(directory: Path) -> dict:

    records = {}

    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records[path.name] = data  # key = "0001.json", "0002.json", ...
        except Exception as e:
            print(f"  [!] Could not parse {path.name}: {e}")

    print(f"[*] Loaded {len(records)} records.")

    return records

def main_DDA(records: dict):

    # VALID RANGES per sensor field
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

    # Programmatic anomaly checks:
    def get_active_fields(sensor_type: str) -> set:

        """Return the set of fields that should be non-zero for this sensor combo."""

        active = set()

        for part in sensor_type.lower().split("/"):
            active.update(SENSOR_FIELDS[part.strip()]) # e.g. {'water_level_meters', 'voltage_supply_v'}

        return active

    def check_programmatic(rec: dict) -> list[str] | None:
        """
        Returns list of anomaly (deterministic).
        Empty list = no programmatic anomaly.
        """

        anomalies = []

        sensor_type = rec["sensor_type"]

        active = get_active_fields(sensor_type)

        for field, (lo, hi) in RANGES.items():

            val = rec[field]

            if field in active:
                if not (lo <= val <= hi):
                    anomalies.append(
                        f"{field}={val} out of range [{lo}, {hi}]"
                    )
            else:
                # Field should be 0 (sensor shouldn't measure it)
                if val != 0:
                    anomalies.append(
                        f"{field}={val} should be 0 for sensor_type='{sensor_type}'"
                    )
        
        if not anomalies:
            return None
        
        return anomalies

    DDA_anomalies_dict = {}   # file_name -> list of anomaly strings

    for file_name, record in records.items():

        anomalies_list = check_programmatic(record)

        if anomalies_list:
            DDA_anomalies_dict[file_name] = anomalies_list

    return DDA_anomalies_dict