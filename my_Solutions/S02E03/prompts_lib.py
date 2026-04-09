
# For prompt to recognize directions for small vision models - WORKS!
# BACK-UP
# vision_prompt = """
# You are a direction detector. Your ONLY job is to identify which cardinal directions have a line segment extending from the CENTER of the image.

# ---
# STEP 1 — LOCATE THE CENTER
# ---
# Find the exact center pixel of the image.

# ---
# STEP 2 — CHECK EACH OF 4 DIRECTIONS
# ---
# From the center, ask YES or NO for each:

#   N (up)    → Does a line leave the center going upward?
#   E (right) → Does a line leave the center going rightward?
#   S (down)  → Does a line leave the center going downward?
#   W (left)  → Does a line leave the center going leftward?

# ---
# WHAT TO IGNORE — CRITICAL
# ---
# * Do NOT look at the overall shape.
# * Do NOT name the shape (corner, L, T, etc.).
# * Do NOT trace the full path of lines.
# * Do NOT include diagonals. Only N, E, S, W are valid.

# Only ask: "Does a line EXIT the center in this direction?"

# ---
# OUTPUT FORMAT — STRICT
# ---
# - Output ONLY the letters of valid directions.
# - No spaces. No punctuation. No explanation. Nothing else.
# - Order does not matter (NE == EN).

# ---
# ALL POSSIBLE OUTCOMES
# ---
# ── 2 directions (6) ──
# Straight vertical                      → NS
# Straight horizontal                    → EW
# Corner up-right                        → NE
# Corner up-left                         → NW
# Corner down-right                      → SE
# Corner down-left                       → SW

# ── 3 directions (4) ──
# T facing down  (open bottom)           → NES  (missing W)
# T facing up    (open top)              → ESW  (missing N)
# T facing right (open right)            → NSW  (missing E)
# T facing left  (open left)             → NEW  (missing S)

# ── 4 directions (1) ──
# Four-way cross                         → NESW
# ---
# FINAL REMINDER
# ---
# You output ONE short string. Nothing before it. Nothing after it.
# """

#------------------------------------------------------------------------------------------------

puzzle_system_prompt = """
You are solving a 3x3 electrical cable rotation puzzle.
You are given TWO states:
- CURRENT state (unsolved)
- TARGET state (solved)

Each cell contains a cable with exits described by compass letters:
N = up, S = down, W = left, E = right

Example:
"NE" means cable connects north (up) and east (right).

---
CABLE TYPES (ALL POSSIBLE SHAPES)
---
── 2 exits (6 types) ──
Straight vertical                      → NS
Straight horizontal                    → EW
Corner up-right                        → NE
Corner up-left                         → NW
Corner down-right                      → SE
Corner down-left                       → SW
── 3 exits (4 types) ──
T-shape (bottom not connected)        → NEW
T-shape (up not connected)            → ESW
T-shape (right not connected)         → NSW   
T-shape (left not connected)          → NES 
── 4 exits (1 type) ──
Four-way cross                         → NESW

---
GRID LAYOUT
---
Cells are addressed as COLUMN (letter) x ROW (number):

     A    |    B    |    C
  --------|---------|--------
1 |  A1   |   B1    |   C1  |
  |-------|---------|-------|
2 |  A2   |   B2    |   C2  |
  |-------|---------|-------|
3 |  A3   |   B3    |   C3  |


Column A = left, Column C = right
Row 1 = top, Row 3 = bottom

START POINT: Electricity enters from the LEFT at point PS (Power Source) → connects into column A
END POINTS:  Electricity must reach exits at Output1, Output2, Output3 on the RIGHT side of column C

---
CRITICAL RULES
---
1. START & END:
Electricity is provided from point X (left of row 3) and must reach all
three exit points 1, 2, 3 (right of rows 1, 2, 3).
No leakages — every cable exit must connect to something. Circut must be closed!

2. ROTATION:
Each rotation = 90° CLOCKWISE
Direction mapping per step:
  N → E → S → W → N

Example:
  NE → ES (1 rotation)
  NE → SW (2 rotations)
  NE → WN (3 rotations)

3. CORE LOGIC (IMPORTANT):
For EACH cell:
- Compare CURRENT exits vs TARGET exits
- If they differ → rotation is REQUIRED
- The difference between CURRENT and TARGET DEFINES the rotation count

This is NOT optional:
You MUST compute how many clockwise rotations transform CURRENT → TARGET

4. MATCHING RULE:
After rotation:
- The set of exits MUST EXACTLY match the TARGET cell
- Order does not matter, but directions must match

5. STRAIGHT LINE RULE:
NS / EW shapes have 2-fold symmetry.
Valid rotation values for straight lines: 0 (unchanged) or 2 (180°) only.

6. VALIDATION (MANDATORY):
After applying ALL rotations:
- Adjacent cells must connect correctly:
  · If a cell has E, its right neighbor must have W
  · If a cell has S, its bottom neighbor must have N
- No broken connections
- No dangling ends
- Full consistent network from A to exits 1, 2, 3

---
OUTPUT FORMAT
---
Return ONLY valid JSON.
No explanations. No markdown.
Include ALL 9 cells.

[
  {"cell": "A1", "rotations": 0},
  {"cell": "B1", "rotations": 2},
  {"cell": "C1", "rotations": 1},
  {"cell": "A2", "rotations": 0},
  {"cell": "B2", "rotations": 3},
  {"cell": "C2", "rotations": 0},
  {"cell": "A3", "rotations": 1},
  {"cell": "B3", "rotations": 0},
  {"cell": "C3", "rotations": 0}
]

Rules:
- rotations ∈ {0, 1, 2, 3}
- EVERY cell must be present exactly once
- Rotation MUST come from CURRENT → TARGET difference
- Do NOT guess — compute via rotation of the cell

RESULT save to JSON as 'rotations.json', use proper tools.

"""

#------------------------------------------------------------------------------------------------

# WORKING TEMPLATE:
# SOLVED:
# puzzle_3x3_input_prompt="""
# ---
# PUZZLE STATES
# ---

# Current (unsolved):

#               A    |    B    |    C
#           ---------|---------|----------
#           |   SE   |   NES   |   NS    |---Output1
#           |--------|---------|-------- |
#           |   EW   |   ESW   |   ESW   |---Output2
#           |--------|---------|-------- |
#      PS---|   NSW  |   NW    |   NE    |---Output3

# TARGET (solved):

#               A    |    B    |    C
#           ---------|---------|----------
#           |   SE   |   ESW   |   EW    |---Output1
#           |--------|---------|-------- |
#           |   NS   |   NES   |   ESW   |---Output2
#           |--------|---------|-------- |
#      PS---|   NEW  |   NW    |   NE    |---Output3

# """

def construct_input_prompt(cord_dict_crnt: dict, cord_dict_solved: dict) -> str:

  return f"""
  ---
  PUZZLE STATES
  ---

  Current state (unsolved):

            A    |    B    |    C
        ---------|---------|----------
        |   {cord_dict_crnt["A1"]:<3}  |   {cord_dict_crnt["B1"]:<3}   |   {cord_dict_crnt["C1"]:<3}   |---Output1
        |--------|---------|-------- |
        |   {cord_dict_crnt["A2"]:<3}  |   {cord_dict_crnt["B2"]:<3}   |   {cord_dict_crnt["C2"]:<3}   |---Output2
        |--------|---------|-------- |
   PS---|   {cord_dict_crnt["A3"]:<3}  |   {cord_dict_crnt["B3"]:<3}   |   {cord_dict_crnt["C3"]:<3}   |---Output3

  TARGET state (solved):

            A    |    B    |    C
        ---------|---------|----------
        |   {cord_dict_solved["A1"]:<3}  |   {cord_dict_solved["B1"]:<3}   |   {cord_dict_solved["C1"]:<3}   |---Output1
        |--------|---------|-------- |
        |   {cord_dict_solved["A2"]:<3}  |   {cord_dict_solved["B2"]:<3}   |   {cord_dict_solved["C2"]:<3}   |---Output2
        |--------|---------|-------- |
   PS---|   {cord_dict_solved["A3"]:<3}  |   {cord_dict_solved["B3"]:<3}   |   {cord_dict_solved["C3"]:<3}   |---Output3

  """
