from dotenv import load_dotenv
import os
import pandas as pd
import requests
from schemas import TaskResultRequest
from typing import Any, Final


load_dotenv()

AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]
BASE_URL: Final[str] = os.environ["BASE_URL"]
VERIFICATION_ENDPOINT: Final[str] = os.environ["VERIFICATION_ENDPOINT"]
DEFAULT_VERIFY_URL: Final[str]  = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"

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