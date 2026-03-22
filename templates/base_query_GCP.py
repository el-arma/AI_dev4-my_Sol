
from dotenv import load_dotenv
from google import genai
import os


load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("GCP_PROJECT_ID"),
    location="europe-west4",
)

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Why is sky blue?"
)

print(resp.text)