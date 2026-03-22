from dotenv import load_dotenv
import os
import pandas as pd
from schemas import WorkersTagging
from suit import fetch_csv_dataset, task_result_verification
from openai import OpenAI
from typing import List, Final

# -------------------------------
# 0. Load API KEYs
# -------------------------------

load_dotenv()

AI_DEV4_API_KEY = os.environ["AI_DEV4_API_KEY"]

# -------------------------------
# 1. Get CSV from Data point
# -------------------------------
BASE_URL: Final[str] = os.environ["BASE_URL"]
DATA_SOURCE_ENDPOINT: Final[str] = os.environ["DATA_SOURCE_ENDPOINT"]

base_data_source_url: str = f"{BASE_URL}/{DATA_SOURCE_ENDPOINT}"

task_name: str = "people"

df = fetch_csv_dataset(task_name, base_data_source_url, AI_DEV4_API_KEY)

df = df.reset_index(drop=True)


# -------------------------------
# 2. Data filtering pipeline
# -------------------------------

# Reference date used for age calculation
ref_date = pd.Timestamp("2026-01-01")

# Build a readable pandas pipeline
df_target_men = (
    df
    # Keep only men
    .query("gender == 'M'")
    
    # Keep only people born in Grudziądz
    .query("birthPlace == 'Grudziądz'")
    
    # Convert birthDate column to datetime
    .assign(
        birthDate=lambda x: pd.to_datetime(x["birthDate"])
    )
    
    # Calculate age in years
    .assign(
        age=lambda x: (ref_date - x["birthDate"]).dt.days // 365
    )
    
    # Filter age range
    .query("20 <= age <= 40")
)

# Convert result to dictionary: {id: job}
json_data = df_target_men["job"].to_dict()


# -------------------------------
# 3. Structured Output in LLM
# -------------------------------

tags: List[str] = [
    "IT",
    "transport",
    "edukacja",
    "medycyna",
    "praca z ludźmi",
    "praca z pojazdami",
    "praca fizyczna",
]

contex_data = json_data


OPEN_API_PROJ_NAME: Final[str] = os.environ["OPEN_API_PROJ_NAME"]

client = OpenAI(
    project=OPEN_API_PROJ_NAME
    # project ID from OpenAI dashboard (to properly count tokens)
    )

system_prompt = f"""
    Assign tags to each worker description.

    Allowed tags:
    {tags}

    Rules:
    - Use only tags from the allowed list
    - A worker may have multiple tags
    - Always return the worker id
    """

response = client.responses.parse(
    model="gpt-4.1",
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": str(contex_data)},
    ],
    text_format=WorkersTagging,
)

LLM_resp = response.output_parsed

# -------------------------------
# 4. Merging back with base df & convert to final JSON
# -------------------------------

json_LLM_resp = LLM_resp.model_dump()

tags_json = json_LLM_resp

df_tags = pd.DataFrame(tags_json["workers"]).set_index("id")

df_final = df_target_men.join(df_tags)

df_final_transport = df_final[df_final["tags"].apply(lambda x: "transport" in x)]

df_final_transport = df_final_transport.reset_index()[[
    "name",
    "surname",
    "gender",
    "birthDate",
    "birthPlace",
    "tags"
    ]].rename(columns={
    "birthDate": "born",
    "birthPlace": "city"
    })

df_final_transport["born"] = pd.to_datetime(df_final_transport["born"]).dt.year

core_result = df_final_transport.to_dict(orient="records")

final_Centrala_res = task_result_verification(task_name, core_result, AI_DEV4_API_KEY)

print(final_Centrala_res)


