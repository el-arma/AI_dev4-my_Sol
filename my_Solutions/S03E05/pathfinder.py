"""
Deterministic pathfinder for the Skolwin messenger mission (AIDEVS S03E05).

ALGORITHM: Breadth-First Search (BFS) over a resource-aware state space.

WHY BFS:
    BFS processes states in order of steps taken, so the first path that
    reaches the goal is guaranteed to have the minimum number of moves.
    Fewer moves = less food consumed — food is the scarcest resource here
    because walk costs 2.5/step and must be used to cross water.

STATE = (row, col, mode, fuel_x10, food_x10)
    - (row, col):   current grid position
    - mode:         active travel mode ('rocket', 'car', 'horse', 'walk')
    - fuel_x10:     remaining fuel x 10, stored as integer to avoid float
                    comparison bugs (e.g. 0.1+0.2 ≠ 0.3 in IEEE-754)
    - food_x10:     remaining food x 10, same reason

PRUNING (Pareto dominance):
    For each (row, col, mode) we maintain a Pareto front of (fuel, food)
    pairs seen so far. A new state is skipped if any existing point has
    BOTH >= fuel AND >= food — that prior state can reach everything the
    new one can, with at least as many resources. This keeps the queue
    small without sacrificing correctness.

DISMOUNT:
    The 'dismount' command is a free action (no resource cost) that
    switches mode from any vehicle to 'walk' at the current position.
    It can happen at most once per journey.

VEHICLE SELECTION:
    All four vehicles are tried as the starting choice. The result with
    the fewest total commands is returned (shorter = fewer steps = less food).

INPUT CONTRACT:
    grid          list[list[str]]  — 10x10 terrain symbols, row-major
    start         (row, col)       — position of the 'S' cell
    goal          (row, col)       — position of the 'G' cell
    initial_fuel  float            — starting fuel (e.g. 10.0)
    initial_food  float            — starting food (e.g. 10.0)
    terrain_cfg   dict             — passability/cost rules per terrain symbol
    vehicle_cfg   dict             — fuel/food costs per vehicle

OUTPUT:
    list[str] ready to POST as 'answer' to /verify, e.g.:
        ["rocket", "up", "right", "right", "dismount", "right"]
    None — if no valid path exists within the resource budget.
"""

from collections import deque

# ---------------------------------------------------------------------------
# Default configuration
# Pass custom dicts to solve() if the API returns different values.
# ---------------------------------------------------------------------------

# Per-terrain rules
# 'passable': set of modes allowed to enter this cell
# 'is_tree':  True → powered vehicles (car, rocket) pay +tree_extra_fuel_x10
TERRAIN_CFG: dict = {
    '.': {'passable': {'rocket', 'car', 'horse', 'walk'}, 'is_tree': False},
    'T': {'passable': {'rocket', 'car', 'horse', 'walk'}, 'is_tree': True},
    'W': {'passable': {'horse', 'walk'},                  'is_tree': False},
    'R': {'passable': set(),                              'is_tree': False},
    'S': {'passable': {'rocket', 'car', 'horse', 'walk'}, 'is_tree': False},
    'G': {'passable': {'rocket', 'car', 'horse', 'walk'}, 'is_tree': False},
}

# Per-vehicle costs, stored x10 (integers) to match internal arithmetic.
# tree_extra_fuel_x10 is added when entering an 'is_tree' cell; only applies
# to modes that actually burn fuel (car, rocket).
VEHICLE_CFG: dict = {
    'rocket': {'fuel_x10': 10, 'food_x10':  1, 'tree_extra_fuel_x10': 2},
    'car':    {'fuel_x10':  7, 'food_x10': 10, 'tree_extra_fuel_x10': 2},
    'horse':  {'fuel_x10':  0, 'food_x10': 16, 'tree_extra_fuel_x10': 0},
    'walk':   {'fuel_x10':  0, 'food_x10': 25, 'tree_extra_fuel_x10': 0},
}

# Cardinal directions only — no diagonals allowed by the task rules.
MOVES: dict = {
    'up':    (-1,  0),
    'down':  ( 1,  0),
    'left':  ( 0, -1),
    'right': ( 0,  1),
}


# ---------------------------------------------------------------------------
# BFS for a single starting vehicle
# ---------------------------------------------------------------------------

def _bfs(
    grid: list,
    vehicle: str,
    start: tuple,
    goal: tuple,
    fuel_x10: int,
    food_x10: int,
    terrain_cfg: dict,
    vehicle_cfg: dict,
) -> list | None:
    """
    Run BFS from `start` to `goal` using `vehicle` as the initial mode.

    Returns the list of move/dismount commands (without the leading vehicle
    name), or None if the goal is unreachable within the resource budget.
    """
    rows, cols = len(grid), len(grid[0])
    sr, sc = start
    gr, gc = goal

    # ------------------------------------------------------------------
    # parent[state] = (predecessor_state, command_that_produced_this_state)
    # Serves double duty: visited-set check + path reconstruction.
    # ------------------------------------------------------------------
    init_state = (sr, sc, vehicle, fuel_x10, food_x10)
    parent: dict = {init_state: (None, None)}
    queue: deque = deque([init_state])

    # ------------------------------------------------------------------
    # Pareto front per (row, col, mode):
    #   list of (fuel, food) pairs that are mutually non-dominated.
    # A state is dominated if an existing point has >= fuel AND >= food.
    # ------------------------------------------------------------------
    pareto: dict = {}  # (row, col, mode) -> list[(fuel_x10, food_x10)]

    def _dominated(key: tuple, fuel: int, food: int) -> bool:
        """Return True if (fuel, food) is dominated by any point on the front."""
        for f, fo in pareto.get(key, []):
            if f >= fuel and fo >= food:
                return True
        return False

    def _update_pareto(key: tuple, fuel: int, food: int) -> None:
        """Add (fuel, food) to the front, removing any point it dominates."""
        pts = pareto.get(key, [])
        # Drop all existing points that the new point strictly dominates
        pts = [(f, fo) for f, fo in pts if not (fuel >= f and food >= fo)]
        pts.append((fuel, food))
        pareto[key] = pts

    # Seed the starting position
    _update_pareto((sr, sc, vehicle), fuel_x10, food_x10)

    # ------------------------------------------------------------------
    # Main BFS loop
    # ------------------------------------------------------------------
    while queue:
        state = queue.popleft()
        row, col, mode, fuel, food = state

        # Goal check — reconstruct path by walking parent pointers backward
        if row == gr and col == gc:
            cmds: list = []
            cur = state
            while parent[cur][0] is not None:
                prev, cmd = parent[cur]
                cmds.append(cmd)
                cur = prev
            cmds.reverse()
            return cmds

        # --------------------------------------------------------------
        # Action A: move in one of the four cardinal directions
        # --------------------------------------------------------------
        for cmd, (dr, dc) in MOVES.items():
            nr, nc = row + dr, col + dc

            # Stay within grid bounds
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue

            terrain = grid[nr][nc]
            t = terrain_cfg[terrain]

            # Current mode must be allowed on this terrain type
            if mode not in t['passable']:
                continue

            # Compute resource cost for this step
            v = vehicle_cfg[mode]
            fuel_cost = v['fuel_x10']
            if t['is_tree']:
                # Tree tile: powered vehicles burn extra fuel on entry
                fuel_cost += v['tree_extra_fuel_x10']
            food_cost = v['food_x10']

            new_fuel = fuel - fuel_cost
            new_food = food - food_cost

            # Skip if this move would exhaust either resource
            if new_fuel < 0 or new_food < 0:
                continue

            new_state = (nr, nc, mode, new_fuel, new_food)

            # Skip if this exact state was already discovered
            if new_state in parent:
                continue

            # Skip if a previously seen state at this (pos, mode) already
            # has at least as many resources (Pareto dominance pruning)
            pk = (nr, nc, mode)
            if _dominated(pk, new_fuel, new_food):
                continue

            _update_pareto(pk, new_fuel, new_food)
            parent[new_state] = (state, cmd)
            queue.append(new_state)

        # --------------------------------------------------------------
        # Action B: dismount — switch from current vehicle to walk.
        # Free action: no fuel or food consumed, position unchanged.
        # Only valid if not already walking.
        # --------------------------------------------------------------
        if mode != 'walk':
            new_state = (row, col, 'walk', fuel, food)
            if new_state not in parent:
                pk = (row, col, 'walk')
                if not _dominated(pk, fuel, food):
                    _update_pareto(pk, fuel, food)
                    parent[new_state] = (state, 'dismount')
                    queue.append(new_state)

    return None  # This vehicle has no valid path to goal


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def solve(
    grid: list,
    start: tuple,
    goal: tuple,
    initial_fuel: float = 10.0,
    initial_food: float = 10.0,
    terrain_cfg: dict = TERRAIN_CFG,
    vehicle_cfg: dict = VEHICLE_CFG,
) -> list | None:
    """
    Find the shortest valid route from start to goal.

    Tries every vehicle in vehicle_cfg as the starting choice and returns
    the command list with the fewest total elements (minimum moves = minimum
    food consumed overall).

    Args:
        grid:         2D list of terrain symbol strings (row-major, 0-indexed).
        start:        (row, col) of the 'S' tile.
        goal:         (row, col) of the 'G' tile.
        initial_fuel: Starting fuel budget (float, e.g. 10.0).
        initial_food: Starting food budget (float, e.g. 10.0).
        terrain_cfg:  Terrain passability/cost rules — override if API changes.
        vehicle_cfg:  Vehicle cost stats — override if API returns new values.

    Returns:
        list[str] — e.g. ["rocket", "up", "right", "dismount", "right", "right"]
        None      — if no path exists within the resource budget.
    """
    # Multiply by 10 and round to get exact integers, avoiding float drift
    fuel_x10 = round(initial_fuel * 10)
    food_x10 = round(initial_food * 10)

    best: list | None = None

    for vehicle in vehicle_cfg:
        path = _bfs(
            grid, vehicle, start, goal,
            fuel_x10, food_x10,
            terrain_cfg, vehicle_cfg,
        )

        if path is None:
            continue

        # Prepend the vehicle-selection command (first element of the answer)
        full = [vehicle] + path

        # Keep the shorter solution (fewer steps = less food consumed)
        if best is None or len(full) < len(best):
            best = full

    return best


def parse_grid(raw_grid: list) -> tuple:
    """
    Scan raw_grid for 'S' (start) and 'G' (goal) positions.

    Args:
        raw_grid: 2D list of terrain symbol strings as returned by /api/maps.

    Returns:
        (grid, start_pos, goal_pos) where positions are (row, col) tuples.

    Raises:
        ValueError if 'S' or 'G' is missing from the grid.
    """
    start = goal = None
    for r, row in enumerate(raw_grid):
        for c, cell in enumerate(row):
            if cell == 'S':
                start = (r, c)
            elif cell == 'G':
                goal = (r, c)

    if start is None or goal is None:
        raise ValueError("Grid must contain exactly one 'S' and one 'G' cell.")

    return raw_grid, start, goal


# ---------------------------------------------------------------------------
# Sanity check — run directly to verify the Skolwin map produces a valid path
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    SKOLWIN = [
        ['.', '.', '.', '.', '.', '.', '.', '.', 'W', 'W'],
        ['.', '.', '.', '.', '.', '.', '.', 'W', 'W', '.'],
        ['.', 'T', '.', '.', '.', '.', 'W', 'W', '.', '.'],
        ['.', '.', '.', '.', '.', '.', 'W', '.', '.', '.'],
        ['.', '.', 'T', '.', '.', '.', 'W', '.', 'G', '.'],
        ['.', '.', '.', '.', 'R', '.', 'W', '.', '.', '.'],
        ['.', '.', '.', 'R', 'R', '.', 'W', 'W', '.', '.'],
        ['S', 'R', '.', '.', '.', '.', '.', 'W', '.', '.'],
        ['.', '.', '.', '.', '.', '.', 'W', 'W', '.', '.'],
        ['.', '.', '.', '.', '.', 'W', 'W', '.', '.', '.'],
    ]

    grid, start, goal = parse_grid(SKOLWIN)
    result = solve(grid, start, goal, initial_fuel=10.0, initial_food=10.0)

    if result is None:
        print("ERROR: No valid path found.")
    else:
        vehicle = result[0]
        moves = [c for c in result[1:] if c != 'dismount']
        has_dismount = 'dismount' in result

        # Compute actual resource usage to verify correctness
        mode = vehicle
        fuel = 10.0
        food = 10.0
        row, col = start
        print(f"Start: {start}, Goal: {goal}")
        print(f"Vehicle: {vehicle}, Dismount used: {has_dismount}")
        for cmd in result[1:]:
            if cmd == 'dismount':
                mode = 'walk'
                print(f"  dismount -> walk  | fuel={fuel:.1f} food={food:.1f}")
                continue
            dr, dc = MOVES[cmd]
            row += dr
            col += dc
            terrain = SKOLWIN[row][col]
            v = VEHICLE_CFG[mode]
            t = TERRAIN_CFG[terrain]
            fc = v['fuel_x10'] / 10
            foc = v['food_x10'] / 10
            if t['is_tree']:
                fc += v['tree_extra_fuel_x10'] / 10
            fuel -= fc
            food -= foc
            print(f"  {cmd:5s} -> ({row},{col}) [{terrain}] | fuel={fuel:.1f} food={food:.1f}")

        print(f"\nFinal position: ({row},{col})  Goal: {goal}")
        print(f"Remaining: fuel={fuel:.1f}  food={food:.1f}")
        print(f"\nAnswer: {result}")
        print(f"Total commands: {len(result)}  (vehicle + {len(result)-1} steps/actions)")
        assert (row, col) == goal, "Did not reach goal!"
        assert fuel >= 0 and food >= 0, "Resource overrun!"
        print("\nOK — path is valid.")
