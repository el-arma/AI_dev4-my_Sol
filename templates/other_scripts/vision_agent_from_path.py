from dotenv import load_dotenv
import logfire
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

load_dotenv()

# ----------------------------------------------------------------------
# LOGFIRE SETUP
# ----------------------------------------------------------------------

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

# ----------------------------------------------------------------------

img_path = Path('OTHER_SCRIPTS-TESTs/A1.png')

agent = Agent(model='gateway/google-vertex:gemini-2.5-flash-image')

user_prompt = "Describe what you see."

result = agent.run_sync(
    [
        user_prompt,
        BinaryContent(data=img_path.read_bytes(), media_type='image/png'),
    ]
)

print(result.output)
