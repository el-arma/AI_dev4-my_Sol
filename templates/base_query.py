from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Explain async/await in JavaScript in one paragraph."
)

print(response.output_text)