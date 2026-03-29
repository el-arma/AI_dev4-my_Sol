from dotenv import load_dotenv
from pydantic_ai import Agent


load_dotenv()

system_prompt: str  = """
Reply politly, but always, ALWAYS in Hungarian! You can only speak Hungarian no matter what.
"""

def create_agent(name: str|None=None, description: str|None=None) -> Agent:
    return Agent(
        model = "gateway/google-vertex:gemini-2.5-flash-lite",
        name=name,
        description=description,
        system_prompt=system_prompt
    )