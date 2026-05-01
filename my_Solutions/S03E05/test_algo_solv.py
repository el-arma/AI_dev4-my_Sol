import heapq
from collections import defaultdict

# =========================
# CONFIG (from your files)
# =========================

BASE_COST = {
    "rocket": {"fuel": 1.0, "food": 0.1},
    "car":    {"fuel": 0.7, "food": 1.0},
    "horse":  {"fuel": 0.0, "food": 1.6},
    "walk":   {"fuel": 0.0, "food": 2.5},
}

INITIAL_FUEL = 10.0
INITIAL_FOOD = 10.0

DIRECTIONS = {
    "up":    (0, -1),
    "down":  (0, 1),
    "left":  (-1, 0),
    "right": (1, 0),
}

# =========================
# HELPERS
# =========================

def in_bounds(x, y):
    return 0 <= x < 10 and 0 <= y < 10

def passable(tile, mode):
    """Check terrain constraints"""
    if tile == "R":
        return False
    if tile == "W" and mode in ["car", "rocket"]:
        return False
    return True

def compute_cost(mode, tile):
    """Compute resource consumption for entering tile"""
    fuel = BASE_COST[mode]["fuel"]
    food = BASE_COST[mode]["food"]

    # Tree penalty
    if tile == "T" and mode in ["car", "rocket"]:
        fuel += 0.2

    return fuel, food

def heuristic(x, y, goal):
    """Admissible heuristic: minimal food consumption"""
    gx, gy = goal
    dist = abs(x - gx) + abs(y - gy)
    return dist * 0.1  # rocket minimal food

# =========================
# PARETO PRUNING
# =========================

def is_dominated(state, visited):
    """
    Check if this state is dominated by an already seen one.
    Dominated = same (x,y,mode) but worse fuel AND food.
    """
    key = (state["x"], state["y"], state["mode"])
    if key not in visited:
        return False

    for (f, food) in visited[key]:
        if f >= state["fuel"] and food >= state["food"]:
            return True

    return False

def add_state(state, visited):
    """
    Add state to Pareto frontier and remove dominated entries.
    """
    key = (state["x"], state["y"], state["mode"])

    new_list = []
    for (f, food) in visited[key]:
        # remove states dominated by new one
        if not (state["fuel"] >= f and state["food"] >= food):
            new_list.append((f, food))

    new_list.append((state["fuel"], state["food"]))
    visited[key] = new_list

# =========================
# CORE SOLVER
# =========================

def solve(grid):
    """
    Returns:
        ["vehicle", "move1", "move2", ...]
    """

    # find start & goal
    start = None
    goal = None

    for y in range(10):
        for x in range(10):
            if grid[y][x] == "S":
                start = (x, y)
            elif grid[y][x] == "G":
                goal = (x, y)

    # priority queue: (priority, counter, state)
    pq = []
    counter = 0

    visited = defaultdict(list)

    # try all starting vehicles (deterministic)
    for vehicle in ["rocket", "car", "horse"]:
        state = {
            "x": start[0],
            "y": start[1],
            "mode": vehicle,
            "fuel": INITIAL_FUEL,
            "food": INITIAL_FOOD,
            "path": [vehicle],
        }

        h = heuristic(state["x"], state["y"], goal)
        heapq.heappush(pq, (h, counter, state))
        counter += 1

    # A*
    while pq:
        _, _, state = heapq.heappop(pq)

        x, y = state["x"], state["y"]

        # GOAL
        if (x, y) == goal:
            return state["path"]

        # pruning
        if is_dominated(state, visited):
            continue

        add_state(state, visited)

        # =====================
        # 1. MOVEMENT
        # =====================
        for move, (dx, dy) in DIRECTIONS.items():
            nx, ny = x + dx, y + dy

            if not in_bounds(nx, ny):
                continue

            tile = grid[ny][nx]

            if not passable(tile, state["mode"]):
                continue

            fuel_cost, food_cost = compute_cost(state["mode"], tile)

            new_fuel = state["fuel"] - fuel_cost
            new_food = state["food"] - food_cost

            if new_fuel < 0 or new_food < 0:
                continue

            new_state = {
                "x": nx,
                "y": ny,
                "mode": state["mode"],
                "fuel": new_fuel,
                "food": new_food,
                "path": state["path"] + [move],
            }

            h = heuristic(nx, ny, goal)

            heapq.heappush(pq, (h, counter, new_state))
            counter += 1

        # =====================
        # 2. DISMOUNT
        # =====================
        if state["mode"] != "walk":
            new_state = {
                "x": x,
                "y": y,
                "mode": "walk",
                "fuel": state["fuel"],
                "food": state["food"],
                "path": state["path"] + ["dismount"],
            }

            heapq.heappush(pq, (heuristic(x, y, goal), counter, new_state))
            counter += 1

    return None  # no solution

grid = [
    list("........WW"),
    list(".......WW."),
    list(".T....WW.."),
    list("......W..."),
    list("..T...W.G."),
    list("....R.W..."),
    list("...RR.WW.."),
    list("SR.....W.."),
    list("......WW.."),
    list(".....WW..."),
]

answer = solve(grid)

print(answer)