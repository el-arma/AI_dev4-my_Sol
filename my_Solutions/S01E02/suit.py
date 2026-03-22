from dotenv import load_dotenv
from functools import wraps
import json
import math
import os
import pandas as pd
import requests
from pathlib import Path
from schemas import TaskResultRequest
from typing import Final, Any


load_dotenv()

AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]
BASE_URL: Final[str] = os.environ["BASE_URL"]
PROJ_BASE_DIR: Final[Path] = Path(__file__).parents[2]
DATA_BANK_PATH: Final[Path] = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank"
VERIFICATION_ENDPOINT = os.environ["VERIFICATION_ENDPOINT"]

def inject_api_key(func):
    @wraps(func)
    def wrapper(url: str, *args, **kwargs):

        if "tutaj-twój-klucz" in url:
            url = url.replace("tutaj-twój-klucz", AI_DEV4_API_KEY)

        return func(url, *args, **kwargs)

    return wrapper

def save_to_json_file(
    data: Any,
    file_name: str,
    *,
    indent: int | None = 2,
    ensure_ascii: bool = False
) -> str | Path:
    """
    Save Python object to JSON file.

    Args:
        data: Any JSON-serializable Python object
        file_name: file name with proper extension
        indent: Pretty-print indentation (None for compact)
        ensure_ascii: Escape non-ASCII characters if True
        overwrite: Allow overwriting existing file

    Returns:
        Path to saved file
    """
    path = DATA_BANK_PATH / file_name

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=indent,
            ensure_ascii=ensure_ascii
        )

    return path

def fetch_csv_dataset(task_name: str, base_url: str, api_key: str) -> pd.DataFrame:
    """
    Fetch CSV dataset from API called "CENTRALA" and return as pandas DataFrame.

    Args:
        task_name: dataset name (e.g. "people")
        base_url: base API url (e.g. "https://api.example.com")
        api_key: AI_DEV4_API_KEY

    Returns:
        pandas DataFrame
    """

    url = f"{base_url}/{api_key}/{task_name}.csv"

    df = pd.read_csv(url)

    return df

@inject_api_key
def fetch_json_data_from_URL(url: str) -> Any:
    """
    Fetch JSON data from a given URL.

    Args:
        url: Full URL to request.

    Returns:
        Parsed JSON response.
    """

    response = requests.get(url)
    response.raise_for_status()

    return response.json()

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

def geo_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate approximate geographic distance between two coordinates.

    The function takes two points defined by latitude and longitude
    and returns the distance between them in kilometers (accuracy ~1 km).

    Args:
        lat1: latitude of the first point
        lon1: longitude of the first point
        lat2: latitude of the second point
        lon2: longitude of the second point

    Returns:
        Distance between the two points in kilometers
    """

    dlat = (lat2 - lat1) * 111
    dlon = (lon2 - lon1) * 111 * math.cos(math.radians(lat1))

    return math.sqrt(dlat**2 + dlon**2)

def geocode_place(place: str) -> dict | None:
    """
    Convert a place description into geographic coordinates using OpenStreetMap Nominatim.

    Args:
        place: Natural language description of a location (e.g. "power plant Tczew Poland").

    Returns:
        Dictionary with latitude and longitude or None if the place was not found.
        Example:
        {
            "lat": 54.0924,
            "lon": 18.7776
        }
    """

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "ai-agent-geocoder"
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    return {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"])
    }

DEFAULT_VERIFY_URL: Final[str] = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"

def task_result_verification(task_name:str, answer: Any, apikey: str = AI_DEV4_API_KEY, 
                     base_url: str = DEFAULT_VERIFY_URL)-> requests.Response:
    """
    Send task result to the Headquarter (also known as CENTRALA or HUB) API for verification.

    Args:
        task_name: name of the task (e.g. "findhim")
        answer: task result (can be list, dict, string, etc., generaly some JSON object)

    Returns:
        API response parsed as JSON

    """

    payload = TaskResultRequest(
        apikey=apikey,
        task=task_name,
        answer=answer
    )

    response = requests.post(
        base_url,
        json=payload.model_dump()
    )

    response.raise_for_status()

    return response.json()