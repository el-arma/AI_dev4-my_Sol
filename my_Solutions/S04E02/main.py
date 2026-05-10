import asyncio
from logger import AgentLogger
from dotenv import load_dotenv
import logfire
from prompts_lib import S04E02_prompts
from pydantic_ai import Agent
from schemas import TurbineScheduleAnswer
from suit import task_result_verification
from token_tracker import CostTracker
from utils import check_API_response, get_multi_unlock_Codes


# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# ======================================================================
# LOGFIRE SETUP & Tracking
# ======================================================================

logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

tt = CostTracker()

# ======================================================================
# AGENTS
# ======================================================================

Smith_log = AgentLogger("Agent_Smith")
Walker_log = AgentLogger("Agent_Walker")

Agent_Smith = Agent(
    model="anthropic:claude-sonnet-4-6",
    name="Agent Smith, specialty: Special Agent",
    description="Heavy Duty Agent",
    tools=[task_result_verification],
    capabilities=[Smith_log.get_hooks()]
)

Agent_Walker = Agent(
    model="openai:gpt-5.4",
    name="Agent_Walker, specialty: Quick Agent",
    description="Quick reliable Agent",
    capabilities=[Walker_log.get_hooks()]
)

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main():

    logfire.info("WF Starts")

    AI_doc_res = None
    turbin_config_not_singed = None

    try:

        logfire.info("Step1 - get the docs")

        AI_doc_res = await Agent_Smith.run(S04E02_prompts["user_prompt_step1"])
        print(AI_doc_res.output)

        logfire.info("Step2 - request the data")

        await asyncio.to_thread(task_result_verification, task_name="windpower", answer={"action": "start"})

        await asyncio.gather(
            asyncio.to_thread(task_result_verification, task_name="windpower", answer={"action": "get", "param": "weather"}),
            asyncio.to_thread(task_result_verification, task_name="windpower", answer={"action": "get", "param": "turbinecheck"}),
            asyncio.to_thread(task_result_verification, task_name="windpower", answer={"action": "get", "param": "powerplantcheck"}),
        )

        response_data = await check_API_response(3, lambda: asyncio.to_thread(
            task_result_verification, task_name="windpower", answer={"action": "getResult"}
            ),
            init_delay=10
        )

        weather_data = next(r for r in response_data if r.get("sourceFunction") == "weather")
        wind_forcast: dict[str, float] = {entry["timestamp"]: entry["windMs"] for entry in weather_data["forecast"]}

        print(wind_forcast)

        logfire.info("Step3 - Check the query")

        turbin_config_not_singed = await Agent_Walker.run(
            S04E02_prompts["user_prompt_step2"] + str(wind_forcast),
            output_type=TurbineScheduleAnswer
        )

        print(turbin_config_not_singed.output.model_dump())

        logfire.info("Step4 - Request to Code Generator")

        config_points = [
            {
                "startDate": timestamp.split(" ")[0],
                "startHour": timestamp.split(" ")[1],
                "windMs": wind_forcast[timestamp],
                "pitchAngle": slot.pitchAngle,
            }
            for timestamp, slot in turbin_config_not_singed.output.answer.configs.items()
        ]

        unlock_responses = await get_multi_unlock_Codes(config_points)
        print(unlock_responses)

        logfire.info("Step5 - Poll for unlock codes")

        response_codes = await check_API_response(len(config_points), lambda: asyncio.to_thread(
            task_result_verification, task_name="windpower", answer={"action": "getResult"}
            )
        )

        print(response_codes)

        logfire.info("Step6 - Build signed config and submit")

        signed_configs = turbin_config_not_singed.output.answer.configs.copy()

        for entry in response_codes:
            if entry.get("code") == 12 and "signedParams" in entry:
                sp = entry["signedParams"]
                ts_key = f"{sp['startDate']} {sp['startHour']}"
                if ts_key in signed_configs:
                    signed_configs[ts_key].unlockCode = entry["unlockCode"]

        final_answer = {
            "action": "config",
            "configs": {
                ts: {
                    "pitchAngle": slot.pitchAngle,
                    "turbineMode": slot.turbineMode,
                    "unlockCode": slot.unlockCode,
                }
                for ts, slot in signed_configs.items()
            }
        }

        print(final_answer)

        submit_result = await asyncio.to_thread(task_result_verification, task_name="windpower", answer=final_answer)
        
        print(submit_result)

        await asyncio.to_thread(task_result_verification, task_name="windpower", answer={"action": "done"})

    finally:

        Smith_log.close()
        Walker_log.close()

        if AI_doc_res is not None:
            tt.sum_tokens(Agent_Smith.model, AI_doc_res.usage())
        if turbin_config_not_singed is not None:
            tt.sum_tokens(Agent_Walker.model, turbin_config_not_singed.usage())

        tt.summary()

    logfire.info("WF FINISH!")

if __name__ == "__main__":

    asyncio.run(main())
