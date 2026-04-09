from dotenv import load_dotenv
from functools import wraps
import json
import math
from markdownify import markdownify as md_trans
import os
import requests
import random
import pandas as pd
from pathlib import Path
from schemas import (TaskResultRequest,
                    )
from session import ContextSessionManager
import time
from urllib.parse import urlparse
from typing import Final, Any, List, Optional, Iterator



load_dotenv()

# API Key:
AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]

# Path:
PROJ_BASE_DIR: Final[Path] = Path(os.environ["PROJ_BASE_DIR"])
DATA_BANK_PATH: Final[Path] = PROJ_BASE_DIR / "my_Solutions/Data_Bank"

# Endpoints:
DATA_SOURCE_ENDPOINT: Final[str] = os.environ["DATA_SOURCE_ENDPOINT"]
VERIFICATION_ENDPOINT: Final[str] = os.environ["VERIFICATION_ENDPOINT"]
MAIL: Final[str] = os.environ["MAIL"]

# URL:
BASE_URL: Final[str] = os.environ["BASE_URL"]
DEFAULT_VERIFY_URL: Final[str] = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"
API_ZMAIL_URL: Final[str] = f"{BASE_URL}/{MAIL}"

# WHITELIST [IMPORTANT]:
whitelisted_URL: List[str] = [
    BASE_URL,
    "https://nominatim.openstreetmap.org",
]

# ==================================================================
# Session
# ==================================================================

session = ContextSessionManager()

# ==================================================================
# Helpers
# ==================================================================

def _check_if_whitelisted(url: str) -> bool:
    """
    Return True ONLY if the URL matches any whitelisted base URL,
    otherwise False.
    """
    
    target = urlparse(url)

    return any(
        target.scheme == base.scheme
        and target.netloc.endswith(base.netloc)
        for base in map(urlparse, whitelisted_URL)
    )

def inject_api_key(func):
    @wraps(func)
    def wrapper(url: str, *args, **kwargs):

        if "tutaj-twój-klucz" in url:
            url = url.replace("tutaj-twój-klucz", AI_DEV4_API_KEY)

        return func(url, *args, **kwargs)

    return wrapper

# ==================================================================
# Tools
# ==================================================================

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

# def geo_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#     """
#     Calculate approximate geographic distance between two coordinates.

#     The function takes two points defined by latitude and longitude
#     and returns the distance between them in kilometers (accuracy ~1 km).

#     Args:
#         lat1: latitude of the first point
#         lon1: longitude of the first point
#         lat2: latitude of the second point
#         lon2: longitude of the second point

#     Returns:
#         Distance between the two points in kilometers
#     """

#     dlat = (lat2 - lat1) * 111
#     dlon = (lon2 - lon1) * 111 * math.cos(math.radians(lat1))

#     return math.sqrt(dlat**2 + dlon**2)

# def geocode_place(place: str) -> dict | None:
#     """
#     Convert a place description into geographic coordinates using OpenStreetMap Nominatim.

#     Args:
#         place: Natural language description of a location (e.g. "power plant Tczew Poland").

#     Returns:
#         Dictionary with latitude and longitude or None if the place was not found.
#         Example:
#         {
#             "lat": 54.0924,
#             "lon": 18.7776
#         }
#     """

#     url = "https://nominatim.openstreetmap.org/search"

#     params = {
#         "q": place,
#         "format": "json",
#         "limit": 1
#     }

#     headers = {
#         "User-Agent": "ai-agent-geocoder"
#     }

#     response = requests.get(url, params=params, headers=headers, timeout=10)
#     response.raise_for_status()

#     data = response.json()

#     if not data:
#         return None

#     return {
#         "lat": float(data[0]["lat"]),
#         "lon": float(data[0]["lon"])
#     }

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

    return response.json()

def wait_for_API(retry_after: int = 15, penalty_seconds: int = 0) -> str:
    """
    Wait after receiving a rate limit error from the API.
    Call this tool when you receive a response with "code": -985 (rate limit exceeded).
    Pass the exact values from the error response.
    
    Args:
        retry_after: seconds to wait, taken directly from the API error response field "retry_after"
        penalty_seconds: additional penalty seconds from the API error response field "penalty_seconds"
    
    Returns:
        Confirmation message that waiting is complete and the agent can retry.
    """
    wait = retry_after + penalty_seconds + random.uniform(1, 3)
    print(f"⏳ Rate limit. Czekam {wait:.1f}s (retry_after={retry_after}, penalty={penalty_seconds})")
    time.sleep(wait)
    return f"Waited {wait:.1f} seconds. You can now retry the previous request."

def fetch_csv_from_URL(task_name: str, apikey: str = AI_DEV4_API_KEY, 
                    base_url: str = BASE_URL) -> Any:
    """
    Fetch CSV dataset from API called "CENTRALA" and return as pandas DataFrame. If url was not provided, 
    Default URL will be used.

    Args:
        task_name: dataset name (e.g. "people")
        base_url: base API url (e.g. "https://api.example.com")
        api_key: AI_DEV4_API_KEY

    Returns:
        pandas DataFrame
    """

    url = f"{base_url}/data/{apikey}/{task_name}.csv"

    df = pd.read_csv(url)

    return df.to_json(orient="records")

# def get_context():

#     "Tool to remember the context beetwen AI Agents runs."

#     # def inner():
#     #     return context  

#     context = [
#     {
#         "code": "i4283",
#         "description": "Handful of fuses in glass tubes, rated between 1A and 30A"
#     },
#     {
#         "code": "i1289",
#         "description": "Pneumatic valve assembly with brass fittings and rubber seals"
#     },
#     {
#         "code": "i2395",
#         "description": "Large industrial fan blade assembly, three blades, aluminum construction"
#     },
#     {
#         "code": "i6047",
#         "description": "Reactor fuel cassette with experimental thorium-based fuel composition"
#     },
#     {
#         "code": "i5546",
#         "description": "Truck-sized leaf spring suspension assembly, heavily worn"
#     },
#     {
#         "code": "i7391",
#         "description": "Reactor fuel cassette containing enriched uranium pellets for portable nuclear power units"
#     },
#     {
#         "code": "i8450",
#         "description": "Collapsible baton made of hardened steel"
#     },
#     {
#         "code": "i8095",
#         "description": "Soldering iron with hand-carved wooden grip, surprisingly effective"
#     },
#     {
#         "code": "i8461",
#         "description": "Small CRT monitor gutted for parts but cathode tube still intact"
#     },
#     {
#         "code": "i4668",
#         "description": "Functional flamethrower with pressurized fuel canister and ignition system"
#     }
#     ]

#     return get_context()


@inject_api_key
def get_png_from_url(url: str, file_name: str) -> None:
    
    """
    Download a PNG file from a URL and save it locally.

    Args:
        url (str): Source URL of the PNG file.
        file_name (str): Name of the output file (keep as .png)

    """
        
    if not _check_if_whitelisted(url):
        raise ValueError(f"URL '{url}' is not allowed (not in whitelist).") 

    response = requests.get(url)

    response.raise_for_status()  # ensure request worked
    
    full_path: Path = DATA_BANK_PATH / file_name

    full_path.parent.mkdir(parents=True, exist_ok=True)

    with full_path.open("wb") as f:
        f.write(response.content)

def post_json_data_to_API(payload: dict, url: str=API_ZMAIL_URL, 
                          apikey: str = AI_DEV4_API_KEY)-> requests.Response:
    
    """
    Send JSON data via POST request and return JSON response.

    Args:
        payload: Data to send as JSON body.
        
    Returns:
        Parsed JSON response.
    """

    if not _check_if_whitelisted(url):
        raise ValueError(f"URL '{url}' is not allowed (not in whitelist).") 

    payload['apikey'] = apikey
    response = requests.post(url, json=payload)

    return response.json()

def save_to_context(content: str) -> None:
    """
    Save any useful data into shared context.

    Args:
        content: Arbitrary data to persist for later steps (e.g. dict, list, str, objects).

    Returns:
        None
    """

    session.save_ctx(content)

    return None

def get_from_context(session: ContextSessionManager) -> Any:
    """
    Retrieve previously stored data from shared execution context.

    Returns:
        Any: The last saved context value.
    """

    return session.get_ctx()

def get_content_from_Website(url: str, file_name: str) -> None:
    """
    Download HTML content from a website, convert it to Markdown, and save it locally.

    Args:
    url (str): Source URL of the website to fetch content from.
    file_name (str): Name of the output file (typically .md).

    """

    if not _check_if_whitelisted(url):
        raise ValueError(f"URL '{url}' is not allowed (not in whitelist).") 
    
    response = requests.get(url)

    response.raise_for_status()

    response.encoding = response.apparent_encoding  # auto-detect
    
    html = response.text

    full_path: Path = DATA_BANK_PATH / file_name

    full_path.parent.mkdir(parents=True, exist_ok=True)

    result = md_trans(html, heading_style="ATX")

    with full_path.open("w", encoding="utf-8") as f:
        f.write(result)


def _txt_chunk_generator(
    full_file_path: Path,
    chunk_size: int = 1000,
) -> Iterator[List[str]]:
    """
    Yield chunks of lines from a txt/log file with optional filtering.

    Args:
        full_file_path: full path to the file
        chunk_size: number of lines per chunk
    """

    chunk: List[str] = []

    with full_file_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")  # FIX

            chunk.append(line)

            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    
    # last chunk
    if chunk:
        yield chunk

def read_txt(
    file_name: str,
    chunk_size: int = 1000,
) -> List[str]:
    
    """
    Read txt file and return a flat list of lines.

    Args:
        file_name: Log file name.

    Returns:
        List of lines.
    """

    result: List[str] = []

    full_file_path: Path = DATA_BANK_PATH / file_name

    for chunk in _txt_chunk_generator(full_file_path, chunk_size):
        result.extend(chunk)

    return result
