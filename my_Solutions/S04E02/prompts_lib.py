from dotenv import load_dotenv
import os
from typing import Final

load_dotenv()

# URLs / credentials:
TASK_NAME: Final[str] = os.environ["S04E02_TASK_NAME"]

# ======================================================================
# S04E02 — Wind Power Scheduler
# ======================================================================

S04E02_prompts = {
    
"user_prompt_step1" : f"""

You are a wind turbine scheduler preparing parameters for the scheduling agent.

use task_result_verification with {{"task":"{TASK_NAME}","answer":{{...}}}}

1. Call `task_result_verification` with {{"action": "get", "param": "documentation"}}.
2. Extract from the response all important information including:
   - Max cutoff wind speed (storm threshold)
   - Min operational wind speed
   - Pitch angle table
   - Turbine power rating
3. Return a concise structured summary of these values for the next AI agent to use as scheduling parameters. No emojis,
no redundant talk, you are passing valuable information, keep it simple and 'dry'.

""", 

"user_prompt_step2" : f"""

You are a wind turbine scheduler preparing proper parameters based on provided documentation.

Analyse all drovided data sources (documentation & Weather Data ):
  Important:
  - weather → hourly windMs:
  - Storm slots: ALL hours where windMs > cutoff_wind → pitchAngle=90, turbineMode=idle
  - Production slot: EXACTLY ONE — the single slot with the HIGHEST windMs in range [min_wind, cutoff_wind]
  
Rules:
- Datetime keys format: "YYYY-MM-DD HH:00:00" (minutes and seconds always zero).
- turbineMode values: "production" | "idle".
- Config structure: ALL storm slots (windMs > cutoff) + EXACTLY ONE production slot (highest windMs ≥ min). Never include multiple production slots.

Here are weather data: 

"""
}
