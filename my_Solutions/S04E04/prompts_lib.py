from dotenv import load_dotenv
import os
from typing import Final

load_dotenv()


# URLs / credentials:
S04E04_TASK_NAME: Final[str] = os.environ["S04E04_TASK_NAME"]
S04E04_NOTES_ZIP_URL: Final[str] = os.environ["S04E04_NOTES_ZIP_URL"]
S04E04_FILE_SYS_DIR: Final[str] = os.environ["S04E04_FILE_SYS_DIR"]

# ======================================================================
# S04E04 — filesystem
# ======================================================================

S04E04_flag_prompt = f"""
You are a data-extraction agent. Your ONLY goal: obtain the flag (FLG:...) from CENTRALA
and save the plan to /workspace/s04e04_plan.json so the next agent can replicate it locally.

## OVERVIEW OF THE REQUIRED FILESYSTEM STRUCTURE

Three top-level directories must exist:

| Directory  | One file per…  | File content                                          |
|------------|----------------|-------------------------------------------------------|
| /miasta    | city           | JSON object: goods the city needs and their quantities (no units, no Polish diacritics) |
| /osoby     | person         | Person's full name + markdown link to their city file |
| /towary    | traded good    | Markdown link to the city that sells it               |

Rules:
- File names: NO Polish diacritics (ą→a, ę→e, ó→o, ś→s, ź/ż→z, ć→c, ń→n, ł→l).
- File name for a city = city name in nominative case, no diacritics.
- File name for a person = FirstName_LastName (underscore, no diacritics).
- File name for a good  = singular nominative in Polish, no diacritics (e.g. "koparka", not "koparki").
- JSON values in /miasta files must also contain no Polish diacritics.
- Quantities are numbers only — strip any unit words.

## PHASE 1 — ACQUIRE DATA

1. Use `download_zip_from_URL` to download the notes archive from:
   {S04E04_NOTES_ZIP_URL}
   Save it as "natan_notes.zip".
   ctx_key="natan_zip", ctx_value="natan_notes.zip", ctx_description="Raw ZIP of Natan notes"

2. Use `extract_zip_file` to unpack it into folder "natan_notes".
   ctx_key="natan_notes_dir", ctx_value="natan_notes", ctx_description="Unpacked Natan notes folder"

3. Read EVERY file in the unpacked folder (use MCP filesystem list_directory + read_file).

## PHASE 2 — EXTRACT AND PLAN

Analyse all notes and build an in-memory plan with three sections:

```
plan = {{
    "miasta": {{
        "<city_name_no_diacritics>": {{"<good_no_diacritics>": <quantity_int>, ...}},
        ...
    }},
    "osoby": {{
        "<FirstName_LastName_no_diacritics>": {{
            "display": "<Full Name>",
            "city_file": "<city_name_no_diacritics>"
        }},
        ...
    }},
    "towary": {{
        "<good_singular_no_diacritics>": "<city_name_no_diacritics>",
        ...
    }}
}}
```

Cross-check: every good in /towary must appear as a key in at least one /miasta file,
and every person in /osoby must reference a city that exists in /miasta.

## PHASE 3 — *** GET THE FLAG *** (API BATCH + VERIFICATION)

Build a single list of operations from the plan above:

```python
operations = [
    {{"action": "createDir",  "path": "/miasta"}},
    {{"action": "createDir",  "path": "/osoby"}},
    {{"action": "createDir",  "path": "/towary"}},
    # one entry per city file:
    {{"action": "createFile", "path": "/miasta/<city>",   "content": "<json_string>"}},
    # one entry per person file:
    {{"action": "createFile", "path": "/osoby/<person>",  "content": "<name_and_link>"}},
    # one entry per good file:
    {{"action": "createFile", "path": "/towary/<good>",   "content": "<link>"}},
]
```

Step 3a — Call `task_result_verification` ONCE with:
- task_name = "filesystem"
- answer    = operations   (ALL operations in a single call, never partial)

Step 3b — After the batch is accepted, call `task_result_verification` once more with:
- task_name = "filesystem"
- answer    = {{"action": "done"}}

CENTRALA will return the flag (FLG:...). CAPTURE AND REPORT IT.

## PHASE 3c — SAVE PLAN FOR NEXT AGENT

After securing the flag, use MCP filesystem write_file to save the plan as JSON:
- path: /workspace/s04e04_plan.json
- content: the full plan dict serialised as JSON (ensure_ascii=true, compact)

This file will be read by the next agent to replicate the structure locally.

## RULES AND CONSTRAINTS

- NEVER send partial batches. The batch in Phase 3 must contain ALL operations at once.
- If the API returns code -985 (rate limit), call `wait_for_API` with the provided values,
  then retry.
- If the API returns an error about existing paths, call reset first:
  task_result_verification(task_name="filesystem", answer={{"action": "reset"}})
  then resend the full batch.
- Strip ALL Polish diacritics from every file name and JSON value before writing.
- Quantities must be plain integers (no units, no decimals).
- Good names in /towary use SINGULAR nominative (e.g. "koparka", not "koparki").

## SUCCESS CONDITION

CENTRALA returns a message containing `FLG:` after the `done` action.
Report the flag and confirm that /workspace/s04e04_plan.json was saved.
"""


S04E04_replicate_prompt = f"""
You are a filesystem replication agent.

Your task: read the plan saved by the previous agent and create the complete local
directory + file structure using MCP filesystem tools.

## STEP 1 — READ THE PLAN

Use MCP filesystem read_file to load:
  /workspace/s04e04_plan.json

Parse the JSON. It has three keys: "miasta", "osoby", "towary".

## STEP 2 — CREATE DIRECTORIES

create_directory  /workspace/miasta
create_directory  /workspace/osoby
create_directory  /workspace/towary

## STEP 3 — CREATE CITY FILES  (/workspace/miasta/<city>)

For each city in plan["miasta"]:
- path: /workspace/miasta/<city_name_no_diacritics>
- content: compact JSON of the goods dict (ASCII-safe, no diacritics in keys or values)

## STEP 4 — CREATE PERSON FILES  (/workspace/osoby/<person>)

For each person in plan["osoby"]:
- path: /workspace/osoby/<FirstName_LastName_no_diacritics>
- content (two lines):
  ```
  <display name>
  [<city_name_no_diacritics>](/miasta/<city_file>)
  ```

## STEP 5 — CREATE GOOD FILES  (/workspace/towary/<good>)

For each good in plan["towary"]:
- path: /workspace/towary/<good_singular_no_diacritics>
- content:
  ```
  [<city_name_no_diacritics>](/miasta/<city_name_no_diacritics>)
  ```

## RULES

- Strip ALL Polish diacritics from every file name and content value.
- Quantities are plain integers.
- Good names use SINGULAR nominative Polish (e.g. "koparka", not "koparki").

## SUCCESS CONDITION

All directories and files created. Report a summary of what was written.
"""
