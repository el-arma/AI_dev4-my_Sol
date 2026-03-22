from agents import create_agent
import asyncio
from pathlib import Path
from typing import Final, List
from schemas import( SurvivorPersData, LocationRequest, 
                    LocationResponse, AccecssRequest, AccecssResponse, 
                    Candidate)
import json
import os
from suit import load_json_file
from utils import sent_multi_async_requests
import logfire


# Configure Logfire
logfire.configure(
    send_to_logfire='if-token-present',  
)
logfire.instrument_pydantic_ai()

Agent_Thompson = create_agent()

# Agent_Smith = create_agent("openai:gpt-5.2")
Agent_Smith = create_agent("claude-sonnet-4-5")

AI_DEV4_API_KEY: Final[str] = os.environ["AI_DEV4_API_KEY"]
PROJ_BASE_DIR: Final[Path] = Path(__file__).parents[2]
S01E02_PP_LIST: Final[str] = os.environ["S01E02_PP_LIST"]
S01E02_LOCATION_URL: Final[str] = os.environ["S01E02_LOCATION_URL"]
S01E02_ACCESS_LVL_URL: Final[str] = os.environ["S01E02_ACCESS_LVL_URL"]

# -------------------------------
# Run
# -------------------------------

if __name__ == "__main__":
    
    task_desc_user_prompt: str = f"""

    1.Pobierz z API Centrali JSON z listą elektrowni z {S01E02_PP_LIST}
    2. Zapisz na dysku jako JSON o nazwie findhim_locations.

    """

    Agent_Thompson.run_sync(task_desc_user_prompt)

    # -------------------------------
    # Get locations
    # -------------------------------

    payloads: List[dict] = []
    requests: List[LocationRequest] = []
    
    location_url: str = S01E02_LOCATION_URL
    source_path = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank" / "survivors.json"
    source_data = load_json_file(source_path)

    for survivor in source_data:

        surv_pers_data = SurvivorPersData(**survivor)

        loc_req = LocationRequest(
            apikey=AI_DEV4_API_KEY,
            name=surv_pers_data.name,
            surname=surv_pers_data.surname,
        )

        requests.append(loc_req)
        payloads.append(loc_req.model_dump())

    results = asyncio.run(sent_multi_async_requests(location_url, payloads))

    final_responses: List[LocationResponse] = []

    for req, res in zip(requests, results):

        response_model = LocationResponse(
            name=req.name,
            surname=req.surname,
            locations=res
        )

        final_responses.append(response_model)

    finala_req_path = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank" / "survivors_location.json"

    with open(finala_req_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in final_responses], f, indent=2, ensure_ascii=False)

    # -------------------------------
    # Get access
    # -------------------------------

    payloads: List[dict] = []
    requests: List[AccecssRequest] = []
    access_url: str = S01E02_ACCESS_LVL_URL
    source_path = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank" / "survivors.json"
    source_data = load_json_file(source_path)

    for survivor in source_data:

        surv_pers_data = SurvivorPersData(**survivor)

        loc_req = AccecssRequest(
            apikey=AI_DEV4_API_KEY,
            name=surv_pers_data.name,
            birthYear=surv_pers_data.born,
            surname=surv_pers_data.surname,
        )

        requests.append(loc_req)
        payloads.append(loc_req.model_dump())

    results = asyncio.run(sent_multi_async_requests(access_url, payloads))

    responses: List[AccecssResponse] = []

    for req, res in zip(requests, results):

        response_model = AccecssResponse(
            name=req.name,
            surname=req.surname,
            accessLevel=res['accessLevel']
        )

        responses.append(response_model)

    finala_req_path = PROJ_BASE_DIR / "my_Solutions" / "Data_Bank" / "survivors_access.json"

    with open(finala_req_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in responses], f, indent=2, ensure_ascii=False)

    task_desc_user_prompt: str = """

    1. Odczytaj z dysku plik JSON findhim_locations.json
    2. Dla każdej z lokacji ustal współrzędne geograficzne (długość, szerokość). 
    3. Zapisz je jako JSON file o nazwie power_plants_geo.json. Poniżej wzór JSON:
        ```"power_plant_name": {
        "locations": [
        {
            "latitude": 49.982,
            "longitude": 19.815
        }
        "code": "PWR7264PL"
        }```

    """

    result = Agent_Smith.run_sync(task_desc_user_prompt)

    task_desc_user_prompt: str = """
    1. Odczytaj z dysku plik JSON power_plants_geo oraz survivors_location.
    2. Ustal która osoba z pliku survivors_location.json znajdowała się najbliżej którejś z elektrowni podanych w pliku power_plants_geo.
    3. Możesz użyć narzędzia geo_distance_km.
    4. Podaj te dane tej osobe, nazwe elektrowni oraz odległość w jakiej od niej była.
    5. Zapisz wynik jako candidate.json zgodnie z podanym formatem
       {
        name: str
        surname: str
        powerPlant: str
        }```
    """

    result = Agent_Smith.run_sync(task_desc_user_prompt)

    task_desc_user_prompt: str = """
    1. Odczytaj z dysku plik JSON candidate oraz survivors_access oraz findhim_locations.json.
    2.Zamień wartość pola powerPlant z nazwy elektrowni na jej kod ('code') w poniższym schemacie odpowiedzi JSON
    i wyśli do weryfikacji z pomocą toola task_result_verification

    task_name = "findhim"

    JSON answer:

    ```
    {
        "name": str,
        "surname": str,
        "accessLevel": int,
        "powerPlant": str
    }
    ```

    """

    result = Agent_Thompson.run_sync(task_desc_user_prompt)

    print(result.output)

