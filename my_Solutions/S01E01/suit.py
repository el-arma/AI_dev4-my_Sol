import pandas as pd
import requests


def fetch_csv_dataset(task_name: str, base_url: str, api_key: str) -> pd.DataFrame:
    """
    Fetch CSV dataset from API called "CENTRALA" and return as pandas DataFrame.

    Args:
        task_name: dataset name (e.g. "people")
        base_url: base API url (e.g. "https://hub.ag3nts.org/data")
        api_key: AI_DEV4_API_KEY

    Returns:
        pandas DataFrame
    """

    url = f"{base_url}/{api_key}/{task_name}.csv"

    df = pd.read_csv(url)

    return df


DEFAULT_VERIFY_URL = "https://hub.ag3nts.org/verify"

def send_task_result(task_name: str, answer, api_key: str, base_url: str = DEFAULT_VERIFY_URL) -> requests.Response:
    """
    Send task result to the AG3NTS verification API.

    The function builds the required JSON payload and sends it
    as a POST request to the verification endpoint.

    Args:
        task_name: name of the task (e.g. "findhim")
        answer: task result (can be list, dict, string, etc., generaly some JSON object)
        api_key: AI_DEV4_API_KEY used for authentication
        base_url: verification endpoint (default: DEFAULT_VERIFY_URL)

    Returns:
        API response parsed as JSON
    """

    payload = {
        "apikey": api_key,
        "task": task_name,
        "answer": answer
    }

    response = requests.post(
        base_url,
        json=payload
    )

    response.raise_for_status()

    return response