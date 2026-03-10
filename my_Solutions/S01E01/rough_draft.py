#%%

# Get CSV from Data point

from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

AI_DEV4_API_KEY = os.getenv("AI_DEV4_API_KEY")

if not AI_DEV4_API_KEY:
    raise ValueError("Missing AI_DEV4_API_KEY in environment variables")

data_source_url = f'https://hub.ag3nts.org/data/{AI_DEV4_API_KEY}/people.csv'

df = pd.read_csv(data_source_url)

df.to_csv('people.csv', index=False)


#%%

# Filtering Data 

import pandas as pd


df = pd.read_csv("people.csv", encoding="utf-8")

df_men = df[df["gender"]=="M"]

df_men_Grudz = df_men[df["birthPlace"]=="Grudziądz"]

df_men_Grudz["birthDate"] = pd.to_datetime(df_men_Grudz["birthDate"])

ref_date_2026 = pd.Timestamp("2026-01-01")

df_men_Grudz["age"] = (ref_date_2026 - df_men_Grudz["birthDate"]).dt.days // 365

df_target_men = df_men_Grudz[(df_men_Grudz["age"] >= 20) & (df_men_Grudz["age"] <= 40)]

json_data = df_target_men['job'].to_dict()

json_data

#%%

# Structured Output

from typing import List

from openai import OpenAI
from pydantic import BaseModel


tags = [
    "IT",
    "transport",
    "edukacja",
    "medycyna",
    "praca z ludźmi",
    "praca z pojazdami",
    "praca fizyczna",
]

data = json_data


class WorkerTags(BaseModel):
    id: int
    tags: List[str]


class WorkersTagging(BaseModel):
    workers: List[WorkerTags]


client = OpenAI()

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
        {"role": "user", "content": str(data)},
    ],
    text_format=WorkersTagging,
)

LLM_resp = response.output_parsed

print(LLM_resp)

#%%

from dotenv import load_dotenv
import os

load_dotenv()

AI_DEV4_API_KEY = os.getenv("AI_DEV4_API_KEY")



#%%

json_LLM_resp = LLM_resp.model_dump()

json_LLM_resp

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


full_api_result = {
    "apikey": AI_DEV4_API_KEY,
    "task": "people",
    "answer": core_result
}

full_api_result


#%%

import requests

url = "https://hub.ag3nts.org/verify"

payload = full_api_result

response = requests.post(
    url,
    json=payload
)

print(response.status_code)
print(response.text)

