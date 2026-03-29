
# %%

# OPENAI form JSON

from openai import OpenAI

client = OpenAI()

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"],
    "additionalProperties": False
}

resp = client.responses.create(
    model="gpt-4.1",
    input="Generate random person",
    text={
        "format": {
            "type": "json_schema",
            "name": "person_schema",
            "schema": schema
        }
    }
)

print(resp.output_text)

# %%

# OPENAI + Pydantic

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class Person(BaseModel):
    name: str
    age: int

resp = client.responses.parse(
    model="gpt-4.1",
    input="Generate random person",
    text_format=Person
)

print(resp.output_parsed)

# %%
from pydantic import BaseModel
from pydantic_ai import Agent

class Person(BaseModel):
    name: str
    age: int

agent = Agent(
    "openai:gpt-4o",
    output_type=Person
)

# for normal *.py
# result = agent.run_sync("Generate a random person")

# for notebooku
result = await agent.run("Generate a random person")

print(result.output)

#%%

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

parser = PydanticOutputParser(pydantic_object=Person)

llm = ChatOpenAI(model="gpt-4o")

prompt = f"""
Generate person.

{parser.get_format_instructions()}
"""

resp = llm.invoke(prompt)

person = parser.parse(resp.content)

print(person)

# %%

# Clasic (old approach)

from openai import OpenAI
import json

client = OpenAI()

prompt = """
Generate a random person.

Return JSON in this format:
{
  "name": "string",
  "age": integer
}
"""

resp = client.responses.create(
    model="gpt-4.1",
    input=prompt
)

text = resp.output_text

data = json.loads(text)

print(data)

# %%

# New Structured Output

from openai import OpenAI

client = OpenAI()

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"],
    "additionalProperties": False
}

resp = client.responses.create(
    model="gpt-4.1",
    input="Generate a random person",
    text={
        "format": {
            "type": "json_schema",
            "name": "person_schema",
            "schema": schema
        }
    }
)

print(resp)
print(resp.text)
print(resp.output_text)