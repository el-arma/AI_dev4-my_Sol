import asyncio
import httpx
from typing import Any
from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Final, List
import json

# -------------------------------
# 0. Load API KEYs
# -------------------------------

load_dotenv()

AI_DEV4_API_KEY= os.environ["AI_DEV4_API_KEY"]
S01E02_LOCATION_URL = os.environ["S01E02_LOCATION_URL"]
PROJ_BASE_DIR: Final[Path] = Path(__file__).parents[2]
DATA_BANK_PATH: Final[Path] = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank" / "survivors.json"

# AUX
def load_json_file(file_name: str | Path) -> Any:
    """
    Load JSON file from disk and return parsed Python object.
    """

    file_name = Path(file_name)

    path = DATA_BANK_PATH / file_name

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def send_request(
    client: httpx.AsyncClient,
    payload: dict[str, Any]
) -> dict[str, Any]:
    response = await client.post(S01E02_LOCATION_URL, json=payload)
    response.raise_for_status()
    return response.json()


async def main(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
        tasks = [
            send_request(client, payload)
            for payload in payloads
        ]

        results = await asyncio.gather(*tasks)

    return results


if __name__ == "__main__":
    
    payloads: List[dict] = []

    source_path = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank" / "survivors.json"

    source_data = load_json_file(source_path)

    for survivor in source_data:

        personal_data = {
        "apikey": AI_DEV4_API_KEY,
        "name": survivor['name'],
        "surname": survivor['surname'],
        "birthYear": survivor['born']
        }

        payloads.append(personal_data)

    results = asyncio.run(main(payloads))

    print(results)