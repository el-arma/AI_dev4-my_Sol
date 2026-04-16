import asyncio
from dotenv import load_dotenv
from DDA import main_DDA, load_sensors_data
from logger import log_agent_run
import logfire
import json
# from mcp_server.mcp_calc_server import fastmcp_server
import pandas as pd
from pathlib import Path
from prompts_lib import sys_prompt_Davis
from pydantic_ai import Agent, BinaryContent, ConcurrencyLimit
# from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from session import ContextSessionManager
from schemas import SensorLogCheck
from suit import (
                download_zip_from_URL,
                extract_zip_file,
                load_json_file,
                save_to_json_file,
                task_result_verification
                    # fetch_csv_from_URL, 
                    # save_to_json_file, 
                    # load_json_file, 
                    # get_png_from_url,
                    # post_json_data_to_API,
                    # save_to_context,
                    # get_from_context,
                    # get_content_from_Website,
                    # read_txt
                )
import os
from utils import short_hash
from typing import Final

# ======================================================================
# LOAD .env
# ======================================================================

load_dotenv()

# Endpoints:
# 

# URL:
S03E01_SENSORS_DATA: Final[str] = os.environ["S03E01_SENSORS_DATA"]

# ======================================================================
# LOGFIRE SETUP
# ======================================================================

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

# ======================================================================
# MCP TOOLSET
# ======================================================================

# toolset = FastMCPToolset(fastmcp_server,
#                         tool_error_behavior="model_retry",
#                         max_retries=2)

# ======================================================================
# TOOLS
# ======================================================================

ToolBox1 = [
            download_zip_from_URL,
            extract_zip_file
            # get_content_from_Website,
            # task_result_verification,
            # get_png_from_url,
            # get_from_context, save_to_context,
            ]

# ToolBox2 = [save_to_context]

# ToolBox3 = [task_result_verification,
#             get_from_context, save_to_context,
#             read_txt]

# ======================================================================
# AGENTS
# ======================================================================

system_prompt: str = "Check avialiable tools, use it if needed."

# GATWAY NO LONGER ACTIVE!!!
# "gateway/google-vertex:gemini-2.5-flash"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

Agent_Thompson = Agent(
    model='gemini-2.5-flash',
    deps_type=ContextSessionManager,
    system_prompt=system_prompt,
    name="Agent Thompson",
    # toolsets=[toolset],
    tools=ToolBox1, 
    retries=1 # number of retires of the tool
)

Agent_Davis = Agent(
    model='openai:gpt-4.1',
    system_prompt=sys_prompt_Davis,
    name="Agent Davis, specialty: quick tasks", 
    output_type=SensorLogCheck,
    # max_concurrency=5,
    max_concurrency=ConcurrencyLimit(max_running=3, max_queued=100)
    # tools=ToolBox2
)

# Agent_Smith = Agent(
#     model='gateway/anthropic:claude-sonnet-4-6',
#     system_prompt=system_prompt,
#     name="Agent Smith, specialty: Special Agent", 
#     tools=ToolBox3
# )

# ======================================================================
# Main WorkFlow
# ======================================================================

async def main(task_name: str):

    logfire.info("WF Starts")

    # ----------------------------------------------------------------------

    logfire.info("Init context session")
    
    ctx_session = ContextSessionManager()

    logfire.info("Step 1")

    user_prompt1 = f"""
    Go to {S03E01_SENSORS_DATA}, and save the zip file from website.
    Then save the full path to the file to the context (key: path_to_unpacked_sensor_data).
    Then upack the zip as folder named 'unpacked_sensors'.
    """
    
    res1 = await Agent_Thompson.run(user_prompt1,
                                    deps=ctx_session
                                    )

    print(f"Agent Thompson says: {res1.output}")

    log_agent_run(res1)

    for key, item in ctx_session.items.items():
        print(f"KEY: {key}")
        print(f"  description: {item.description}")
        print(f"  value: {item.value}")

    #------------------------------------------------------------------------


    # DETERMINISTIC ANOMALY DETECTOR
    #----------------------------------------------------------------------

    upack_data_folder_path = Path(r"my_Solutions\Data_Bank\unpacked_sensors")

    sensors_data_records = load_sensors_data(upack_data_folder_path)
    
    save_to_json_file(sensors_data_records, 'ALL_sensors_logs_in_one.json')
 
    DDA_anomalies_dict: dict = main_DDA(sensors_data_records)

    # checkpoint:
    save_to_json_file(DDA_anomalies_dict, 'DDA_full.json')
    
    DDA_file_list = list(DDA_anomalies_dict.keys())
    
    # checkpoint:
    save_to_json_file((DDA_file_list), 'DDA_file_list.json')

    #----------------------------------------------------------------------

    unique_logs = {}

    for file_name, log_content in sensors_data_records.items():
        
        # if file name is already on the anomally list then no poin in sending it to LLM
        if file_name in DDA_file_list:

            # skip this one file_name:
            continue

        op_note: str = log_content["operator_notes"]
        
        hash_id = short_hash(op_note)

        unique_logs[hash_id] = op_note
    
    # checkpoint:
    save_to_json_file(unique_logs, 'unique_op_notes.json')


    #----------------------------------------------------------------------

    # cut uniqe logs to batches
    items = list(unique_logs.items())

    batch_size: int = 50

    batches = [
        # batch2json:
        json.dumps(dict(items[i:i+batch_size]), ensure_ascii=False)
        for i in range(0, len(items), batch_size)
    ]

    results = []

    for batch in batches:
        results.append(await Agent_Davis.run(batch))
        await asyncio.sleep(5)

    # save to json
    LLM_output = [
        {"batch": idx, "output": res.output.model_dump()}
        for idx, res in enumerate(results)
    ]

    # checkpoint:
    save_to_json_file(LLM_output, 'LLM_output_Davis.json')
    
    # MERG RESULTS:
    #----------------------------------------------------------------------

    # --- Load ALL logs ---
    with open(r"my_Solutions\Data_Bank\ALL_sensors_logs_in_one.json", "r", encoding="utf-8") as f:
        all_logs_raw = json.load(f)

    df_logs = (
        pd.DataFrame.from_dict(all_logs_raw, orient="index")
        .reset_index(names="file_name")[["file_name", "operator_notes"]]
    )

    # --- Load unique operator notes (hash -> text) ---
    with open(r"my_Solutions\Data_Bank\unique_op_notes.json", "r", encoding="utf-8") as f:
        unique_notes_raw = json.load(f)

    df_notes = pd.DataFrame(
        list(unique_notes_raw.items()),
        columns=["hash_id", "operator_notes"]
    )

    # --- Load LLM flags (hash -> flag) ---
    with open(r"my_Solutions\Data_Bank\LLM_output_Davis.json", "r", encoding="utf-8") as f:
        llm_raw = json.load(f)

    df_flags = pd.DataFrame([
        {"hash_id": hash_id, "flag": flag}
        for batch in llm_raw
        for hash_id, flag in batch["output"]["logs_batch"].items()
    ])

    # --- Attach flags to unique notes ---
    df_notes_flagged = df_notes.merge(df_flags, on="hash_id", how="left")

    # --- Propagate flags to all logs ---
    df_logs_flagged = df_logs.merge(
        df_notes_flagged[["operator_notes", "flag"]],
        on="operator_notes",
        how="left"
    )

    # --- Extract anomalous file names ---
    anomaly_files = df_logs_flagged[df_logs_flagged["flag"] == True]["file_name"].to_list()

    # --- Load existing DDA list ---
    with open(r"my_Solutions\Data_Bank\DDA_file_list.json", "r", encoding="utf-8") as f:
        dda_files = json.load(f)

    # --- Merge and deduplicate ---
    final_list = list(set(dda_files + anomaly_files))

    save_to_json_file(final_list, 'S03E01_final_list.json')

    final_ans = {
        "recheck": final_list
    }

    #----------------------------------------------------------------------

    final_res = task_result_verification(task_name, final_ans)

    print(final_res)

    logfire.info("WF FINISH!")

if __name__ == "__main__":
    
    task_name: str = "evaluation"
    
    asyncio.run(main(task_name))