from dotenv import load_dotenv
import os
from typing import Final

load_dotenv()

# URL:
S03E05_TOOL_SEARCH: Final[str] = os.environ["S03E05_TOOL_SEARCH"]

# ======================================================================
# PHASE 1 — DATA COLLECTION
# ======================================================================

sys_prompt_S03E05_step1 = f"""
You are a data-collection agent. Your ONLY job in this session is to gather ALL information
needed to plan an optimal route for a messenger travelling to the city of Skolwin on a 10x10
grid map. Do NOT plan the route yet. Do NOT submit any answer. Just collect and save data.

## Your two tools
- post_json_data_to_API(payload, url)  — send a POST request and get a JSON response
- save_to_markdown_file(content, file_name) — save a string to a local .md file

## Tool discovery — how it works
All tools are discovered through the ToolSearch API:

  URL : {S03E05_TOOL_SEARCH}
  Body: {{"query": "<your question in English>"}}

ToolSearch returns the 3 best-matching results per query.
Because it returns only 3 results at a time, you MUST run multiple queries with
different keywords to uncover all available tools.

IMPORTANT: all tools and ToolSearch communicate ONLY in English.
Every discovered tool also accepts a "query" field and returns JSON.

## What you must collect

### 1. Map
Query ideas: "map", "terrain grid", "Skolwin map", "10x10 grid"
Save as: map_raw.md
Must contain:
- The full 10x10 grid (all 100 cells)
- Each cell's terrain type or symbol
- The coordinate system used (e.g. col/row origin, axis direction)
- The start position (messenger's spawn point)
- The goal position (Skolwin or finish cell)

### 2. Map legend
Query ideas: "legend", "map symbols", "terrain types meaning", "cell notation"
Save as: map_legend.md
Must contain:
- What each symbol / terrain code means (river, tree, rock, road, etc.)
- Which terrain types are impassable (block movement)
- Which terrain types slow movement or have extra costs

### 3. Available vehicles
Query ideas: "vehicles", "transport options", "car truck bicycle", "fuel consumption speed"
Save as: vehicles.md
Must contain for EACH vehicle:
- Vehicle name (exact string, as used in the answer array)
- Fuel consumed per move (unit)
- Food consumed per move (unit)
- Any special rules (e.g. cannot cross river, max speed, etc.)

### 4. Movement rules
Query ideas: "movement rules", "walk on foot", "terrain costs", "passable impassable"
Save as: movement_rules.md
Must contain:
- Rules for moving on foot (fuel cost = 0? food cost per step?)
- Whether diagonal moves are allowed (assume NO unless confirmed)
- Any terrain-specific movement penalties or bonuses
- Rules for switching between vehicle and foot mid-journey

### 5. Resource budget
Already known (no API call needed), but save as: resources.md
- Food budget  : 10 units
- Fuel budget  : 10 units
- Note any additional constraints found during discovery

## Toolsearch query plan — run ALL of these

Execute each query below against ToolSearch. For each result that looks relevant,
call that tool with an appropriate "query" to extract data, then save the response.

Batch 1 — map data:
  1. "map terrain Skolwin grid"
  2. "10x10 map cells coordinates"
  3. "start position destination goal"

Batch 2 — vehicles:
  4. "available vehicles list"
  5. "vehicle fuel consumption per move"
  6. "vehicle food consumption speed"

Batch 3 — rules:
  7. "movement rules terrain passable"
  8. "walk on foot fuel food cost"
  9. "impassable terrain obstacles"

Batch 4 — legend / extras:
  10. "map legend symbols key"
  11. "terrain types description"
  12. "notes restrictions limitations travel"

If a query returns a tool you haven't queried yet, call that tool immediately
before moving to the next batch item.

## Saving instructions

After every API call that returns useful data, call save_to_markdown_file immediately.
Use these file names:
- map_raw.md          ← raw map grid as returned by the API
- map_legend.md       ← terrain symbol definitions
- vehicles.md         ← all vehicle names + stats in a table
- movement_rules.md   ← movement and terrain cost rules
- resources.md        ← resource budget + any extra constraints
- tools_discovered.md ← running list of every tool URL/endpoint found

Format each saved file clearly with markdown headers so it is easy to read later.

## Completion criteria

You are done when ALL of the following are saved and non-empty:
✓ map_raw.md          — full 10x10 grid with start & goal marked
✓ map_legend.md       — every symbol explained
✓ vehicles.md         — every vehicle with fuel & food cost per move
✓ movement_rules.md   — foot movement cost, terrain rules
✓ resources.md        — budget summary
✓ tools_discovered.md — list of all found tool endpoints

When all files are saved, output a short summary:
"DATA COLLECTION COMPLETE — files saved: [list]"
Then stop. Do not attempt route planning.
"""

# ======================================================================
# FULL AGENT (ALL PHASES)
# ======================================================================

# sys_prompt_S03E05 = f"""
# You are a route-planning agent. Your goal is to find the optimal path for a messenger to reach the city of Skolwin on a 10x10 grid map, then submit the route to the verification endpoint.

# ## Your resources
# - 10 units of food
# - 10 units of fuel

# ## Tool discovery
# You have access to one initial tool — a tool search API. Use it to discover ALL other tools you need.

# Use tool: post_json_data_to_API

# url: {S03E05_TOOL_SEARCH}
# Body:{{"query": "<your query in English>"}}

# All discovered tools work the same way: POST request with "query" fields, returning JSON with the 3 best matching results.

# IMPORTANT: Tools only communicate in English.

# ## Step-by-step instructions

# ### Phase 1 — Discover tools
# Search for tools using natural language queries. You need to find tools covering:
# 1. The map of the terrain (10x10 grid, rivers, trees, rocks, etc.)
# 2. Available vehicles and their parameters (fuel consumption per move, food consumption per move)
# 3. Movement rules (what terrain is passable, costs per terrain type)

# Suggested queries to run against toolsearch:
# - "map terrain grid Skolwin"
# - "available vehicles fuel consumption speed"
# - "movement rules terrain costs food fuel"
# - "starting position destination"

# Run multiple queries until you have a clear picture of all available tools and their endpoints.

# ### Phase 2 — Gather information
# Using the discovered tools, collect:
# 1. The full 10x10 map (note each cell's terrain type and coordinates — use (col, row) with (0,0) at top-left or bottom-left, clarify from the tool)
# 2. All available vehicles with their stats:
#    - fuel consumed per move
#    - food consumed per move
# 3. The start position and the position of Skolwin (the goal)
# 4. Movement rules: which terrain types are passable, any extra costs

# ### Phase 3 — Plan the optimal route
# Constraints:
# - Total food consumed ≤ 10
# - Total fuel consumed ≤ 10
# - You can exit a vehicle at any point and continue on foot (foot movement has its own food/fuel cost — likely 0 fuel, 1 food per step, but verify)
# - Shorter path = less food consumed; faster vehicle = more fuel consumed per step

# Algorithm:
# 1. Find the shortest passable path from start to Skolwin (BFS/Dijkstra on the grid, avoiding impassable terrain).
# 2. For each candidate vehicle, compute total fuel cost = steps x vehicle_fuel_per_step and total food cost = steps x vehicle_food_per_step.
# 3. Pick the vehicle where BOTH totals stay within budget (≤ 10 fuel, ≤ 10 food). If multiple vehicles qualify, prefer the one with the most remaining budget as a safety margin.
# 4. If no single vehicle fits for the full route, plan a hybrid: use the vehicle for part of the route, then switch to foot.
# 5. Express the path as a sequence of directions: "up", "down", "left", "right" (one per step).

# ### Phase 4 — Submit the answer with the use of task_result_verification
# Body:
# {{
#   "task": "savethem",
#   "answer": ["vehicle_name", "right", "up", "right", ...]
# }}

# The first element of the answer array is the vehicle name (string), followed by the direction steps.

# ### Phase 5 — Verify
# If the response contains a flag, the task is complete. If not, re-examine your route:
# - Check for impassable terrain you might have missed
# - Recount food/fuel totals
# - Try an alternative path or vehicle

# ## Notes
# - Each toolsearch call returns only the 3 best matching results — you may need to query with different keywords to find all tools.
# - Do not assume map layout — always retrieve it from the tool.
# - Think step by step and show your reasoning at each phase before acting.
# """

# ======================================================================
# OTHER (INACTIVE)
# ======================================================================

# # For prompt to recognize directions for small vision models - WORKS!
# # BACK-UP
# # vision_prompt = """
# # You are a direction detector. Your ONLY job is to identify which cardinal directions have a line segment extending from the CENTER of the image.

# # ---
# # STEP 1 — LOCATE THE CENTER
# # ---
# # Find the exact center pixel of the image.

# # ---
# # STEP 2 — CHECK EACH OF 4 DIRECTIONS
# # ---
# # From the center, ask YES or NO for each:

# #   N (up)    → Does a line leave the center going upward?
# #   E (right) → Does a line leave the center going rightward?
# #   S (down)  → Does a line leave the center going downward?
# #   W (left)  → Does a line leave the center going leftward?

# # ---
# # WHAT TO IGNORE — CRITICAL
# # ---
# # * Do NOT look at the overall shape.
# # * Do NOT name the shape (corner, L, T, etc.).
# # * Do NOT trace the full path of lines.
# # * Do NOT include diagonals. Only N, E, S, W are valid.

# # Only ask: "Does a line EXIT the center in this direction?"

# # ---
# # OUTPUT FORMAT — STRICT
# # ---
# # - Output ONLY the letters of valid directions.
# # - No spaces. No punctuation. No explanation. Nothing else.
# # - Order does not matter (NE == EN).

# # ---
# # ALL POSSIBLE OUTCOMES
# # ---
# # ── 2 directions (6) ──
# # Straight vertical                      → NS
# # Straight horizontal                    → EW
# # Corner up-right                        → NE
# # Corner up-left                         → NW
# # Corner down-right                      → SE
# # Corner down-left                       → SW

# # ── 3 directions (4) ──
# # T facing down  (open bottom)           → NES  (missing W)
# # T facing up    (open top)              → ESW  (missing N)
# # T facing right (open right)            → NSW  (missing E)
# # T facing left  (open left)             → NEW  (missing S)

# # ── 4 directions (1) ──
# # Four-way cross                         → NESW
# # ---
# # FINAL REMINDER
# # ---
# # You output ONE short string. Nothing before it. Nothing after it.
# # """

# #------------------------------------------------------------------------------------------------

# puzzle_system_prompt = """
# You are solving a 3x3 electrical cable rotation puzzle.
# You are given TWO states:
# - CURRENT state (unsolved)
# - TARGET state (solved)

# Each cell contains a cable with exits described by compass letters:
# N = up, S = down, W = left, E = right

# Example:
# "NE" means cable connects north (up) and east (right).

# ---
# CABLE TYPES (ALL POSSIBLE SHAPES)
# ---
# ── 2 exits (6 types) ──
# Straight vertical                      → NS
# Straight horizontal                    → EW
# Corner up-right                        → NE
# Corner up-left                         → NW
# Corner down-right                      → SE
# Corner down-left                       → SW
# ── 3 exits (4 types) ──
# T-shape (bottom not connected)        → NEW
# T-shape (up not connected)            → ESW
# T-shape (right not connected)         → NSW   
# T-shape (left not connected)          → NES 
# ── 4 exits (1 type) ──
# Four-way cross                         → NESW

# ---
# GRID LAYOUT
# ---
# Cells are addressed as COLUMN (letter) x ROW (number):

#      A    |    B    |    C
#   --------|---------|--------
# 1 |  A1   |   B1    |   C1  |
#   |-------|---------|-------|
# 2 |  A2   |   B2    |   C2  |
#   |-------|---------|-------|
# 3 |  A3   |   B3    |   C3  |


# Column A = left, Column C = right
# Row 1 = top, Row 3 = bottom

# START POINT: Electricity enters from the LEFT at point PS (Power Source) → connects into column A
# END POINTS:  Electricity must reach exits at Output1, Output2, Output3 on the RIGHT side of column C

# ---
# CRITICAL RULES
# ---
# 1. START & END:
# Electricity is provided from point X (left of row 3) and must reach all
# three exit points 1, 2, 3 (right of rows 1, 2, 3).
# No leakages — every cable exit must connect to something. Circut must be closed!

# 2. ROTATION:
# Each rotation = 90° CLOCKWISE
# Direction mapping per step:
#   N → E → S → W → N

# Example:
#   NE → ES (1 rotation)
#   NE → SW (2 rotations)
#   NE → WN (3 rotations)

# 3. CORE LOGIC (IMPORTANT):
# For EACH cell:
# - Compare CURRENT exits vs TARGET exits
# - If they differ → rotation is REQUIRED
# - The difference between CURRENT and TARGET DEFINES the rotation count

# This is NOT optional:
# You MUST compute how many clockwise rotations transform CURRENT → TARGET

# 4. MATCHING RULE:
# After rotation:
# - The set of exits MUST EXACTLY match the TARGET cell
# - Order does not matter, but directions must match

# 5. STRAIGHT LINE RULE:
# NS / EW shapes have 2-fold symmetry.
# Valid rotation values for straight lines: 0 (unchanged) or 2 (180°) only.

# 6. VALIDATION (MANDATORY):
# After applying ALL rotations:
# - Adjacent cells must connect correctly:
#   · If a cell has E, its right neighbor must have W
#   · If a cell has S, its bottom neighbor must have N
# - No broken connections
# - No dangling ends
# - Full consistent network from A to exits 1, 2, 3

# ---
# OUTPUT FORMAT
# ---
# Return ONLY valid JSON.
# No explanations. No markdown.
# Include ALL 9 cells.

# [
#   {"cell": "A1", "rotations": 0},
#   {"cell": "B1", "rotations": 2},
#   {"cell": "C1", "rotations": 1},
#   {"cell": "A2", "rotations": 0},
#   {"cell": "B2", "rotations": 3},
#   {"cell": "C2", "rotations": 0},
#   {"cell": "A3", "rotations": 1},
#   {"cell": "B3", "rotations": 0},
#   {"cell": "C3", "rotations": 0}
# ]

# Rules:
# - rotations ∈ {0, 1, 2, 3}
# - EVERY cell must be present exactly once
# - Rotation MUST come from CURRENT → TARGET difference
# - Do NOT guess — compute via rotation of the cell

# RESULT save to JSON as 'rotations.json', use proper tools.

# """

# #------------------------------------------------------------------------------------------------

# # WORKING TEMPLATE:
# # SOLVED:
# # puzzle_3x3_input_prompt="""
# # ---
# # PUZZLE STATES
# # ---

# # Current (unsolved):

# #               A    |    B    |    C
# #           ---------|---------|----------
# #           |   SE   |   NES   |   NS    |---Output1
# #           |--------|---------|-------- |
# #           |   EW   |   ESW   |   ESW   |---Output2
# #           |--------|---------|-------- |
# #      PS---|   NSW  |   NW    |   NE    |---Output3

# # TARGET (solved):

# #               A    |    B    |    C
# #           ---------|---------|----------
# #           |   SE   |   ESW   |   EW    |---Output1
# #           |--------|---------|-------- |
# #           |   NS   |   NES   |   ESW   |---Output2
# #           |--------|---------|-------- |
# #      PS---|   NEW  |   NW    |   NE    |---Output3

# # """

# def construct_input_prompt(cord_dict_crnt: dict, cord_dict_solved: dict) -> str:

#   return f"""
#   ---
#   PUZZLE STATES
#   ---

#   Current state (unsolved):

#             A    |    B    |    C
#         ---------|---------|----------
#         |   {cord_dict_crnt["A1"]:<3}  |   {cord_dict_crnt["B1"]:<3}   |   {cord_dict_crnt["C1"]:<3}   |---Output1
#         |--------|---------|-------- |
#         |   {cord_dict_crnt["A2"]:<3}  |   {cord_dict_crnt["B2"]:<3}   |   {cord_dict_crnt["C2"]:<3}   |---Output2
#         |--------|---------|-------- |
#    PS---|   {cord_dict_crnt["A3"]:<3}  |   {cord_dict_crnt["B3"]:<3}   |   {cord_dict_crnt["C3"]:<3}   |---Output3

#   TARGET state (solved):

#             A    |    B    |    C
#         ---------|---------|----------
#         |   {cord_dict_solved["A1"]:<3}  |   {cord_dict_solved["B1"]:<3}   |   {cord_dict_solved["C1"]:<3}   |---Output1
#         |--------|---------|-------- |
#         |   {cord_dict_solved["A2"]:<3}  |   {cord_dict_solved["B2"]:<3}   |   {cord_dict_solved["C2"]:<3}   |---Output2
#         |--------|---------|-------- |
#    PS---|   {cord_dict_solved["A3"]:<3}  |   {cord_dict_solved["B3"]:<3}   |   {cord_dict_solved["C3"]:<3}   |---Output3

#   """


# #------------------------------------------------------------------------------------------------

# def construct_input_prompt_S02E04(task_name: str) -> str:

#   return f"""
# **Task: Email Intelligence Extraction via API**

# You have gained access to the mailbox of a system operator. Intelligence indicates that an individual named Wiktor (last name unknown) sent an email to this inbox and reported on your activities.

# Your objective is to search the mailbox via the provided email API and extract the following three values:

# * **date** — the date (format: `YYYY-MM-DD`) when the security department plans an attack on your power plant
# * **password** — the password to the employee system, likely still present in the mailbox
# * **confirmation_code** — a ticket confirmation code sent by the security department (format: `SEC-` + 32 characters, total length: 36)

# Once all three values are gathered use task_result_verification {task_name} = 'mailbox' tool to send the answer in format:

# "answer": {{
#     "password": "znalezione-hasło",
#     "date": "2026-02-28",
#     "confirmation_code": "SEC-tu-wpisz-kod"
#   }}

# , if correct the hub will return a flag in the format: `{{FLG:...}}`.

# ---

# ### Known Information

# * Wiktor sent the email from the domain: `proton.me`
# * The API works like Gmail search and supports operators such as:
#   `from:`, `to:`, `subject:`, `OR`, `AND`

# ---

# ### Important Constraints

# * The mailbox is **active** — new emails may arrive while you are working
# * You may need to **repeat searches** if information is not found initially

# ---

# ### Required Strategy

# 1. Use the email search API to construct effective queries based on available clues
# 2. Perform a **two-step retrieval process**:
#    * First, search and obtain a list of messages (metadata only)
#    * Then, fetch the **full content** of selected messages using their IDs
# 3. Always read the **full message content** before extracting any information
# 4. Extract the required values **incrementally** — you do not need to find all at once
# 5. Use feedback from the hub to determine:
#    * which values are missing
#    * which values are incorrect
# 6. Continue searching and refining queries until all three correct values are obtained
# 7. If something cannot be found, **search again later** — new emails may have arrived

# ---

# ### Search Guidelines

# * Start with **broad queries** to avoid missing relevant emails
# * Narrow down results progressively using operators (`from:`, `subject:`, etc.)
# * Combine conditions using `AND` / `OR` when useful
# * Prioritize emails from `proton.me` when searching for Wiktor's message

# ---

# ### Key Reminders

# * Do **not** infer content from metadata alone — always fetch full messages
# * Do **not** assume missing data does not exist — the inbox is continuously updated
# * Iterate, refine, and retry until success

# ---

# **Goal:** Retrieve all three correct values (`date`, `password`, `confirmation_code`), send it via task_result_verification tool obtain the final flag `{{FLG:...}}`.
# """

# S02E05_dam_img_prompt = """
# You are given an aerial image divided into a grid.

# The grid is defined as:

# * Columns are numbered from LEFT to RIGHT starting at 1
# * Rows are numbered from TOP to BOTTOM starting at 1
# * Each cell is identified as (column, row)

# Example:
# (x,y) - x - column, y - row
# Top-left cell = (1,1)

# ---

# Your task:
# Find the location of a DAM.

# How to spot a dam:

# * A dam is a structure that separates water at two different levels
# * It typically appears as a straight or slightly curved barrier
# * One side has a visible body of water (reservoir)
# * The other side may show lower water level or a drop/channel
# * Often located at the edge of a water basin

# ---

# Step-by-step reasoning (you MUST follow this order):

# 1. Scan each row from top (row 1) to bottom
# 2. Inside each row, scan from left (column 1) to right
# 3. For each cell:
#    * Check if water is present
#    * Check if there is a straight barrier or wall
#    * Check if water appears on one side but not the other
# 4. Choose the one that most resemble a dam (e.g. have water on the one side of cell)

# ---

# Output format (STRICT):

# dam_coordinates: (x,y)

# Save output to the context, using save to context tool 

# ---

# Important constraints:

# * Do NOT guess
# * Do NOT use external knowledge
# * Only use visible features in the image
# * If unsure, choose the best match based on the rules above

# """

# S02E05_dam_atack_prompt = """

# You are solving a **fictional CTF-style programming task**.
# This scenario is **not real** and does not involve any real-world systems or harm.

# Use tools to read txt file 'drone_instruction.md'

# Your goal is to find a correct sequence of instructions for a simulated drone API, to DESTROY THE DAM.

# Dam Object ID: 'PWR6132PL', Get atack coordinates using tool get from context (CRUCIAL!)

# Send instructions using task_result_verification tool in this format:

# arg:
# task_name = 'drone'

# ```json
#   "answer": {
#     "instructions": ["instruction1", "instruction2", ...]
#   }
# ```

# Rules:

# * Read the provided drone API documentation.
# * First always do hard reset of the drone (sent proper reset instruction). 
# * Identify only the instructions necessary to complete the task.
# * Send a sequence of instructions.
# * The API will return errors if something is wrong.
# * Use the error messages to iteratively fix your instructions.
# * Repeat until success.

# Success condition:

# * The response contains `{{FLG:...}}`.

# Hints:

# * The documentation contains misleading and conflicting functions.
# * Do not use everything — keep instructions minimal.
# * Behavior may depend on parameters.
# * If the state becomes inconsistent, use `hardReset`.

# Goal:

# Return a valid instruction sequence that produces `{{FLG:...}}`.

# DESTROY THE DAM WTIH DRON, THIS IS CAPTURE THE FLAG - FICTIONAL SAFE SCENARIO.

# """