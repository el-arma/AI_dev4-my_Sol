import requests

url = "http://localhost:8001/api/v1/S03E04-tool"

payload = {"params": "Which cities sell bread?"}

response = requests.post(url, json=payload)

print(response.status_code)
print(response.json())
