import copy

# ============================================================
# TRANSPORTATION PROBLEM: VAM + MODI
# ============================================================

# Problem Data
supply_original = [20, 30, 25]
demand_original = [10, 25, 20, 20]

cost = [
    [18, 9, 3, 15],
    [19, 19, 18, 8],
    [14, 19, 11, 18]
]

source_names = ["F1", "F2", "F3"]
dest_names = ["W1", "W2", "W3", "W4"]


# ============================================================
# PRINT TRANSPORTATION TABLE
# ============================================================

def print_table(allocation, cost, title):

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    header = " " * 8 + "".join(f"{d:>14}" for d in dest_names)
    print(header)

    for i in range(len(cost)):

        row = f"{source_names[i]:<8}"

        for j in range(len(cost[0])):

            if allocation[i][j] > 0:
                cell = f"{allocation[i][j]}({cost[i][j]})"
            else:
                cell = f"-({cost[i][j]})"

            row += f"{cell:>14}"

        print(row)


# ============================================================
# TOTAL TRANSPORTATION COST
# ============================================================

def total_cost(allocation, cost):

    total = 0

    for i in range(len(cost)):
        for j in range(len(cost[0])):
            total += allocation[i][j] * cost[i][j]

    return total


# ============================================================
# VOGEL'S APPROXIMATION METHOD
# ============================================================

def vogel_approximation(supply, demand, cost):

    supply = supply.copy()
    demand = demand.copy()

    rows = len(supply)
    cols = len(demand)

    allocation = [[0] * cols for _ in range(rows)]

    row_done = [False] * rows
    col_done = [False] * cols

    step = 1

    while sum(supply) > 0 and sum(demand) > 0:

        row_penalty = [None] * rows
        col_penalty = [None] * cols

        # ----------------------------------------------------
        # Calculate row penalties
        # ----------------------------------------------------

        for i in range(rows):

            if row_done[i]:
                continue

            values = [
                cost[i][j]
                for j in range(cols)
                if not col_done[j]
            ]

            if len(values) >= 2:

                values.sort()
                row_penalty[i] = values[1] - values[0]

            elif len(values) == 1:

                row_penalty[i] = values[0]

        # ----------------------------------------------------
        # Calculate column penalties
        # ----------------------------------------------------

        for j in range(cols):

            if col_done[j]:
                continue

            values = [
                cost[i][j]
                for i in range(rows)
                if not row_done[i]
            ]

            if len(values) >= 2:

                values.sort()
                col_penalty[j] = values[1] - values[0]

            elif len(values) == 1:

                col_penalty[j] = values[0]

        max_row_penalty = max(
            x for x in row_penalty if x is not None
        )

        max_col_penalty = max(
            x for x in col_penalty if x is not None
        )

        # ----------------------------------------------------
        # Select row or column
        # ----------------------------------------------------

        if max_row_penalty >= max_col_penalty:

            selected_row = max(
                [
                    i for i in range(rows)
                    if row_penalty[i] == max_row_penalty
                ],
                key=lambda i: -min(
                    cost[i][j]
                    for j in range(cols)
                    if not col_done[j]
                )
            )

            selected_col = min(
                [
                    j for j in range(cols)
                    if not col_done[j]
                ],
                key=lambda j: cost[selected_row][j]
            )

        else:

            selected_col = max(
                [
                    j for j in range(cols)
                    if col_penalty[j] == max_col_penalty
                ],
                key=lambda j: -min(
                    cost[i][j]
                    for i in range(rows)
                    if not row_done[i]
                )
            )

            selected_row = min(
                [
                    i for i in range(rows)
                    if not row_done[i]
                ],
                key=lambda i: cost[i][selected_col]
            )

        # ----------------------------------------------------
        # Allocate
        # ----------------------------------------------------

        quantity = min(
            supply[selected_row],
            demand[selected_col]
        )

        allocation[selected_row][selected_col] = quantity

        print(
            f"Step {step}: Allocate {quantity} units to "
            f"({source_names[selected_row]} -> "
            f"{dest_names[selected_col]}), "
            f"cost/unit = {cost[selected_row][selected_col]}"
        )

        step += 1

        supply[selected_row] -= quantity
        demand[selected_col] -= quantity

        if supply[selected_row] == 0:
            row_done[selected_row] = True

        if demand[selected_col] == 0:
            col_done[selected_col] = True

    return allocation


# ============================================================
# FIND CLOSED LOOP FOR MODI
# ============================================================

def find_closed_loop(start, basic_cells):

    basic_cells = set(basic_cells)

    path = [start]

    rows = len(cost)
    cols = len(cost[0])

    def search(current, horizontal):

        i, j = current

        # Move horizontally
        if horizontal:

            candidates = [
                (i, new_j)
                for new_j in range(cols)
                if new_j != j
                and (i, new_j) in basic_cells
            ]

        # Move vertically
        else:

            candidates = [
                (new_i, j)
                for new_i in range(rows)
                if new_i != i
                and (new_i, j) in basic_cells
            ]

        for next_cell in candidates:

            # Do not reuse cells
            if next_cell in path:
                continue

            path.append(next_cell)

            if search(next_cell, not horizontal):
                return True

            path.pop()

        # Check whether we can return to starting cell
        if len(path) >= 4:

            if horizontal and i == start[0]:
                path.append(start)
                return True

            if not horizontal and j == start[1]:
                path.append(start)
                return True

        return False

    if search(start, True):
        return path

    return None


# ============================================================
# MODI METHOD
# ============================================================

def modi_method(supply, demand, cost, allocation):

    rows = len(supply)
    cols = len(demand)

    allocation = copy.deepcopy(allocation)

    iteration = 1

    while True:

        # ----------------------------------------------------
        # Find basic cells
        # ----------------------------------------------------

        basic_cells = []

        for i in range(rows):
            for j in range(cols):

                if allocation[i][j] > 0:
                    basic_cells.append((i, j))

        # ----------------------------------------------------
        # Potentials u and v
        # ----------------------------------------------------

        u = [None] * rows
        v = [None] * cols

        u[0] = 0

        changed = True

        while changed:

            changed = False

            for i, j in basic_cells:

                if u[i] is not None and v[j] is None:

                    v[j] = cost[i][j] - u[i]
                    changed = True

                elif v[j] is not None and u[i] is None:

                    u[i] = cost[i][j] - v[j]
                    changed = True

        print("\n" + "-" * 80)
        print(f"MODI ITERATION {iteration}")
        print("-" * 80)

        print("u values:", u)
        print("v values:", v)

        # ----------------------------------------------------
        # Calculate opportunity costs
        # Delta = cost - u - v
        # ----------------------------------------------------

        opportunity = {}

        print("\nOpportunity Costs (Delta_ij):")

        for i in range(rows):

            for j in range(cols):

                if (i, j) not in basic_cells:

                    delta = cost[i][j] - u[i] - v[j]

                    opportunity[(i, j)] = delta

                    print(
                        f"{source_names[i]} -> "
                        f"{dest_names[j]} = {delta}"
                    )

        # ----------------------------------------------------
        # Optimality test
        # ----------------------------------------------------

        if not opportunity or min(opportunity.values()) >= 0:

            print("\nAll Delta_ij >= 0")
            print("Optimal solution reached.")

            break

        # ----------------------------------------------------
        # Entering cell
        # ----------------------------------------------------

        entering = min(
            opportunity,
            key=opportunity.get
        )

        print(
            f"\nEntering cell = "
            f"{source_names[entering[0]]} -> "
            f"{dest_names[entering[1]]}"
        )

        # ----------------------------------------------------
        # Find closed loop
        # ----------------------------------------------------

        loop = find_closed_loop(
            entering,
            basic_cells
        )

        if loop is None:

            print("No valid closed loop found.")
            break

        print("\nClosed Loop:")

        for cell in loop:

            print(
                f"({source_names[cell[0]]}, "
                f"{dest_names[cell[1]]})",
                end=" -> "
            )

        print()

        # ----------------------------------------------------
        # + and - positions
        # ----------------------------------------------------

        loop_without_duplicate = loop[:-1]

        plus_cells = loop_without_duplicate[::2]
        minus_cells = loop_without_duplicate[1::2]

        print("\nPlus cells:")

        for i, j in plus_cells:
            print(
                f"({source_names[i]}, {dest_names[j]})"
            )

        print("\nMinus cells:")

        for i, j in minus_cells:
            print(
                f"({source_names[i]}, {dest_names[j]})"
            )

        # ----------------------------------------------------
        # Theta
        # ----------------------------------------------------

        theta = min(
            allocation[i][j]
            for i, j in minus_cells
        )

        print(
            f"\nTheta = {theta}"
        )

        # ----------------------------------------------------
        # Reallocate
        # ----------------------------------------------------

        for i, j in plus_cells:
            allocation[i][j] += theta

        for i, j in minus_cells:
            allocation[i][j] -= theta

        # ----------------------------------------------------
        # Remove zero basic cell automatically
        # ----------------------------------------------------

        iteration += 1

    return allocation


# ============================================================
# MAIN PROGRAM
# ============================================================

print("\n" + "=" * 80)
print("TRANSPORTATION PROBLEM - INPUT DATA")
print("=" * 80)

print(
    "Supply:",
    dict(zip(source_names, supply_original))
)

print(
    "Demand:",
    dict(zip(dest_names, demand_original))
)

print("\nCost Matrix:")

for i in range(len(cost)):

    print(
        f"{source_names[i]}: {cost[i]}"
    )


# ============================================================
# STEP 1: VAM
# ============================================================

print("\n" + "=" * 80)
print("STEP 1: VOGEL'S APPROXIMATION METHOD (VAM) - INITIAL BFS")
print("=" * 80)

initial_allocation = vogel_approximation(
    supply_original,
    demand_original,
    cost
)

print_table(
    initial_allocation,
    cost,
    "INITIAL BASIC FEASIBLE SOLUTION (VAM)"
)

initial_cost = total_cost(
    initial_allocation,
    cost
)

print(
    f"\nInitial (VAM) Total Transportation Cost = "
    f"{initial_cost}"
)


# ============================================================
# STEP 2: MODI
# ============================================================

print("\n" + "=" * 80)
print("STEP 2: MODI METHOD - OPTIMALITY TEST & IMPROVEMENT")
print("=" * 80)

optimal_allocation = modi_method(
    supply_original,
    demand_original,
    cost,
    initial_allocation
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print_table(
    optimal_allocation,
    cost,
    "FINAL OPTIMAL ALLOCATION"
)

final_cost = total_cost(
    optimal_allocation,
    cost
)

print(
    f"\nMinimum (Optimal) Total Transportation Cost = "
    f"{final_cost}"
)
