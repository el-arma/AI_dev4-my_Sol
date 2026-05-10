import asyncio
import base64
import hashlib
import httpx
import random
from typing import Any, Final

# S04E02
import os
from dotenv import load_dotenv


load_dotenv()

async def send_request(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, Any]
) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json()

async def sent_multi_async_requests(url: str, payloads: Any) -> Any:

    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
        tasks = [
            send_request(client, url, payload)
            for payload in payloads
        ]

        results = await asyncio.gather(*tasks)

    return results

def hash_the_flag(flag_name: str):
    return hashlib.sha256(flag_name.encode()).hexdigest()

def short_hash(text: str, length: int = 6) -> str:
    
    # Normalize text (optional but recommended)
    text = text.strip().lower()

    digest = hashlib.sha256(text.encode("utf-8")).digest()
    
    # Base64 -> shorter than hex
    short = base64.urlsafe_b64encode(digest).decode("utf-8")
    
    return short[:length]

# ======================================================================
# S04E02 — Wind Turbine Scheduler
# ======================================================================

async def check_API_response(expected_replies: int, custom_req_fn,
                              init_delay: int=0 ,timeout: int=40):

    """
    Adaptive polling:
    - Slow at the beginning
    - Faster near target time
    """

    start = asyncio.get_running_loop().time()

    TARGET_TIME = 20

    MIN_DELAY = 0.110   # max speed = 110 ms

    response_data = []

    while True:

            response = await custom_req_fn()

            if response.get("code") != 11:
                response_data.append(response)
                
                if len(response_data) == expected_replies:
                    return response_data

            elapsed = asyncio.get_running_loop().time() - start

            if elapsed > timeout:
                raise TimeoutError("API did not return result in time")

            # --- dynamic delay (faster as we approach target) ---
            if elapsed < TARGET_TIME:
                progress = elapsed / TARGET_TIME
                delay = init_delay * (1 - progress) + MIN_DELAY * progress
            else:
                delay = MIN_DELAY  # stay at max speed after target

            # jitter (0–20%)
            jitter = delay * random.uniform(0, 0.2)

            # hard floor protection (never faster than MIN_DELAY parameter)
            sleep_time = max(delay + jitter, MIN_DELAY)

            await asyncio.sleep(sleep_time)


# API Key:
AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]

# Endpoints:
VERIFICATION_ENDPOINT: Final[str] = os.environ["VERIFICATION_ENDPOINT"]

# URL:
BASE_URL: Final[str] = os.environ["BASE_URL"]
DEFAULT_VERIFY_URL: Final[str] = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"

async def get_multi_unlock_Codes(config_points: list[dict]) -> list[dict]:
    
    """
    Fire multiple unlockCodeGenerator requests simultaneously.
    Call this ONCE instead of N sequential unlockCodeGenerator calls.

    Args:
        config_points: list of dicts, each with keys:
            startDate (str, YYYY-MM-DD), startHour (str, HH:00:00),
            windMs (float), pitchAngle (int)

    Returns:
        List of API acknowledgment responses (one per config point, order preserved).
    """

    payloads = [
        {
            "apikey": AI_DEV4_API_KEY,
            "task": "windpower",
            "answer": {
                "action": "unlockCodeGenerator",
                "startDate": cp["startDate"],
                "startHour": cp["startHour"],
                "windMs": cp["windMs"],
                "pitchAngle": cp["pitchAngle"],
            },
        }
        for cp in config_points
    ]

    return list(await sent_multi_async_requests(DEFAULT_VERIFY_URL, payloads))