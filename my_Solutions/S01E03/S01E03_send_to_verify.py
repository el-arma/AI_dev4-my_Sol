
# %%

from dotenv import load_dotenv
import os
import requests
from uuid import uuid4

load_dotenv()

AI_DEV4_API_KEY = os.environ["AI_DEV4_API_KEY"]
BASE_URL = os.environ["BASE_URL"]
VERIFICATION_ENDPOINT = os.environ["VERIFICATION_ENDPOINT"]
DEFAULT_VERIFY_URL = f"{BASE_URL}/{VERIFICATION_ENDPOINT}"

short_id = uuid4().hex[:8]

task_ver_url = DEFAULT_VERIFY_URL

my_backend_url = "https://power-plant-delivery-service-966550094456.europe-central2.run.app/api/v1/friendly-ear"

def test_ask_agent():

    payload = {
        "apikey": AI_DEV4_API_KEY,
        "task": "proxy",
        "answer": {
            "url": my_backend_url,
            "sessionID": short_id
        }
    }

    response = requests.post(task_ver_url, json=payload)

    return response.json()

test_ask_agent()

# %%

import requests

def check_for_flag():

    my_backend_url = "https://power-plant-delivery-service-966550094456.europe-central2.run.app//check-flag"

    res = requests.get(my_backend_url)

    return res.json()

check_for_flag()