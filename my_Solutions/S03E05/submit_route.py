"""
Direct submission for S03E05 — savethem task.

Route analysis:
  Start:  S = (col=0, row=7)
  Goal:   G = (col=8, row=4)

  Optimal path (11 moves, crosses W at col=6,row=4):
    up, right, right, up, right, up, right, right, right, right, right

  Vehicle: rocket
    - Moves 1-10 as rocket: 10 fuel, 1.0 food
    - Move 11 on foot (fuel depleted): 0 fuel, 2.5 food
    - Total: 10/10 fuel, 3.5/10 food
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY: str = os.environ["AI_DEV4_API_KEY"]
VERIFY_URL: str = f"{os.environ['BASE_URL']}/{os.environ['VERIFICATION_ENDPOINT']}"

ANSWER = ['rocket', 'up', 'up', 'up', 'right', 'right', 'right', 'right', 'right', 'dismount', 'right', 'right', 'right']

def main() -> None:
    payload = {
        "apikey": API_KEY,
        "task": "savethem",
        "answer": ANSWER
    }

    print(f"Submitting to: {VERIFY_URL}")
    print(f"Answer: {ANSWER}")

    response = requests.post(VERIFY_URL, json=payload)
    result = response.json()

    print(f"\nStatus: {response.status_code}")
    print(f"Response: {result}")

if __name__ == "__main__":
    main()
