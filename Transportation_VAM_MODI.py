from fractions import Fraction


def print_table(cost, allocation, supply, demand, title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)

    for i in range(len(cost)):
        row = []

        for j in range(len(cost[0])):
            if allocation[i][j] is None:
                row.append("-")
            elif allocation[i][j] == 0:
                row.append("0")
            else:
                row.append(str(allocation[i][j]))

        print(f"F{i+1}: {row} | Supply = {supply[i]}")

    print("Demand:", demand)


def penalty(values):
    values = sorted(values)

    if len(values) >= 2:
        return values[1] - values[0]

    return values[0]


def find_penalties(cost, active_rows, active_cols):
    row_penalty = {}

    for i in active_rows:
        vals = [cost[i][j] for j in active_cols]
        row_penalty[i] = penalty(vals)

    col_penalty = {}

    for j in active_cols:
        vals = [cost[i][j] for i in active_rows]
        col_penalty[j] = penalty(vals)

    return row_penalty, col_penalty


def add_basic_without_cycle(basic, cell, m, n):
    r, c = cell

    graph = [[] for _ in range(m + n)]

    for i, j in basic:
        graph[i].append(m + j)
        graph[m + j].append(i)

    start = r
    target = m + c

    stack = [start]
    visited = set()

    while stack:
        node = stack.pop()

        if node == target:
            return False

        if node in visited:
            continue

        visited.add(node)

        for nxt in graph[node]:
            if nxt not in visited:
                stack.append(nxt)

    return True


def ensure_non_degenerate(allocation, basic, m, n):
    required = m + n - 1

    while len(basic) < required:

        chosen = None

        for i in range(m):
            for j in range(n):

                if (i, j) in basic:
                    continue

                if add_basic_without_cycle(basic, (i, j), m, n):
                    chosen = (i, j)
                    break

            if chosen:
                break

        if chosen is None:
            raise Exception("Could not create a non-cyclic basis.")

        basic.add(chosen)

        if allocation[chosen[0]][chosen[1]] is None:
            allocation[chosen[0]][chosen[1]] = Fraction(0)


def vam(cost, supply, demand):
    m = len(cost)
    n = len(cost[0])

    supply = list(map(Fraction, supply))
    demand = list(map(Fraction, demand))

    allocation = [[None for _ in range(n)] for _ in range(m)]

    active_rows = set(range(m))
    active_cols = set(range(n))

    basic = set()

    while active_rows and active_cols:

        row_penalty, col_penalty = find_penalties(
            cost,
            active_rows,
            active_cols
        )

        candidates = []

        for i, p in row_penalty.items():
            candidates.append(("row", i, p))

        for j, p in col_penalty.items():
            candidates.append(("col", j, p))

        max_penalty = max(x[2] for x in candidates)

        candidates = [
            x for x in candidates
            if x[2] == max_penalty
        ]

        # Tie-breaking: choose the line whose cheapest cell has
        # the smallest cost
        best = None

        for typ, index, p in candidates:

            if typ == "row":
                cells = [(cost[index][j], index, j)
                         for j in active_cols]
            else:
                cells = [(cost[i][index], i, index)
                         for i in active_rows]

            cells.sort()

            candidate = cells[0]

            if best is None or candidate[0] < best[0]:
                best = candidate

        _, i, j = best

        amount = min(supply[i], demand[j])

        allocation[i][j] = amount
        basic.add((i, j))

        supply[i] -= amount
        demand[j] -= amount

        # Both exhausted simultaneously
        if supply[i] == 0 and demand[j] == 0:

            # Keep row active and remove column.
            # Degeneracy will be handled after VAM.
            active_cols.remove(j)
            active_rows.discard(i)

        elif supply[i] == 0:
            active_rows.remove(i)

        elif demand[j] == 0:
            active_cols.remove(j)

    # Convert unused cells to zero for display
    for i in range(m):
        for j in range(n):
            if allocation[i][j] is None:
                allocation[i][j] = Fraction(0)

    # Remove accidental zero basics if basis is too large
    basic = {
        cell for cell in basic
        if allocation[cell[0]][cell[1]] > 0
    }

    ensure_non_degenerate(allocation, basic, m, n)

    return allocation, basic


def calculate_potentials(cost, basic):
    m = len(cost)
    n = len(cost[0])

    u = [None] * m
    v = [None] * n

    u[0] = Fraction(0)

    changed = True

    while changed:
        changed = False

        for i, j in basic:

            if u[i] is not None and v[j] is None:
                v[j] = cost[i][j] - u[i]
                changed = True

            elif u[i] is None and v[j] is not None:
                u[i] = cost[i][j] - v[j]
                changed = True

    # In case the basis is disconnected
    for i in range(m):
        if u[i] is None:
            u[i] = Fraction(0)

            changed = True

            while changed:
                changed = False

                for r, c in basic:

                    if u[r] is not None and v[c] is None:
                        v[c] = cost[r][c] - u[r]
                        changed = True

                    elif u[r] is None and v[c] is not None:
                        u[r] = cost[r][c] - v[c]
                        changed = True

    for j in range(n):
        if v[j] is None:
            v[j] = Fraction(0)

    return u, v


def calculate_deltas(cost, basic, u, v):
    m = len(cost)
    n = len(cost[0])

    delta = [[None for _ in range(n)] for _ in range(m)]

    for i in range(m):
        for j in range(n):

            if (i, j) not in basic:
                delta[i][j] = (
                    cost[i][j] - u[i] - v[j]
                )

    return delta


def find_loop(basic, start, m, n):
    # Find a closed alternating row-column loop
    # starting from entering cell.

    basic_with_start = set(basic)
    basic_with_start.add(start)

    def dfs(path, horizontal):
        current = path[-1]

        if len(path) >= 4 and current == start:
            return path

        i, j = current

        if horizontal:
            candidates = [
                cell for cell in basic_with_start
                if cell[0] == i and cell != current
            ]
        else:
            candidates = [
                cell for cell in basic_with_start
                if cell[1] == j and cell != current
            ]

        for nxt in candidates:

            if nxt == start and len(path) >= 4:
                return path + [start]

            if nxt in path:
                continue

            result = dfs(
                path + [nxt],
                not horizontal
            )

            if result:
                return result

        return None

    return dfs([start], True)


def improve(allocation, basic, entering, loop):
    signs = {}

    for k, cell in enumerate(loop[:-1]):
        if k % 2 == 0:
            signs[cell] = "+"
        else:
            signs[cell] = "-"

    minus_values = []

    for cell, sign in signs.items():

        if sign == "-":
            i, j = cell
            minus_values.append(allocation[i][j])

    theta = min(minus_values)

    for cell, sign in signs.items():

        i, j = cell

        if sign == "+":
            allocation[i][j] += theta

        else:
            allocation[i][j] -= theta

    # Entering cell becomes basic
    basic.add(entering)

    # Remove zero basic cells
    for cell in list(basic):
        i, j = cell

        if allocation[i][j] == 0 and cell != entering:
            basic.remove(cell)

    return theta


def transportation_cost(cost, allocation):
    total = Fraction(0)

    for i in range(len(cost)):
        for j in range(len(cost[0])):
            total += cost[i][j] * allocation[i][j]

    return total


def modi(cost, allocation, basic):
    iteration = 0

    while True:

        iteration += 1

        print_table(
            cost,
            allocation,
            [
                sum(allocation[i][j] for j in range(len(cost[0])))
                for i in range(len(cost))
            ],
            [
                sum(allocation[i][j] for i in range(len(cost)))
                for j in range(len(cost[0]))
            ],
            f"MODI ITERATION {iteration}"
        )

        ensure_non_degenerate(
            allocation,
            basic,
            len(cost),
            len(cost[0])
        )

        u, v = calculate_potentials(cost, basic)

        print("\nU values:", u)
        print("V values:", v)

        delta = calculate_deltas(
            cost,
            basic,
            u,
            v
        )

        print("\nDelta table:")

        for i in range(len(cost)):
            row = []

            for j in range(len(cost[0])):
                if (i, j) in basic:
                    row.append("B")
                else:
                    row.append(str(delta[i][j]))

            print(row)

        negative = []

        for i in range(len(cost)):
            for j in range(len(cost[0])):

                if delta[i][j] is not None and delta[i][j] < 0:
                    negative.append(
                        (delta[i][j], i, j)
                    )

        if not negative:
            print("\nAll Δij >= 0.")
            print("Solution is OPTIMAL.")

            return allocation

        # Most negative delta
        _, ei, ej = min(negative)

        entering = (ei, ej)

        print(
            f"\nEntering cell: F{ei+1}W{ej+1}"
        )

        loop = find_loop(
            basic,
            entering,
            len(cost),
            len(cost[0])
        )

        if loop is None:
            raise Exception("No closed loop found.")

        print("\nClosed loop:")

        for cell in loop:
            print(
                f"F{cell[0]+1}W{cell[1]+1}",
                end=" -> "
            )

        print()

        theta = improve(
            allocation,
            basic,
            entering,
            loop
        )

        print("\nTheta =", theta)

        print(
            "New transportation cost =",
            transportation_cost(cost, allocation)
        )


if __name__ == "__main__":

    # CASE STUDY

    cost = [
        [18, 9, 3, 15],
        [19, 19, 18, 8],
        [14, 19, 11, 18]
    ]

    supply = [20, 30, 25]
    demand = [10, 25, 20, 20]

    allocation, basic = vam(
        cost,
        supply,
        demand
    )

    print_table(
        cost,
        allocation,
        supply,
        demand,
        "VAM INITIAL BASIC FEASIBLE SOLUTION"
    )

    print(
        "\nInitial Transportation Cost =",
        transportation_cost(cost, allocation)
    )

    final_allocation = modi(
        cost,
        allocation,
        basic
    )

    print_table(
        cost,
        final_allocation,
        supply,
        demand,
        "FINAL OPTIMAL SOLUTION"
    )

    print(
        "\nMinimum Transportation Cost =",
        transportation_cost(cost, final_allocation)
    )
