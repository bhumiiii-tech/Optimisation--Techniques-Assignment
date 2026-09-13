from fractions import Fraction


class Term:
    # Represents a*M + b
    def __init__(self, m=0, b=0):
        self.m = Fraction(m)
        self.b = Fraction(b)

    def __add__(self, other):
        return Term(self.m + other.m, self.b + other.b)

    def __sub__(self, other):
        return Term(self.m - other.m, self.b - other.b)

    def __neg__(self):
        return Term(-self.m, -self.b)

    def __mul__(self, x):
        x = Fraction(x)
        return Term(self.m * x, self.b * x)

    __rmul__ = __mul__

    def __truediv__(self, x):
        x = Fraction(x)
        return Term(self.m / x, self.b / x)

    def is_positive(self):
        if self.m != 0:
            return self.m > 0
        return self.b > 0

    def is_negative(self):
        if self.m != 0:
            return self.m < 0
        return self.b < 0

    def is_zero(self):
        return self.m == 0 and self.b == 0

    def __str__(self):
        if self.m == 0:
            return str(self.b)

        if self.b == 0:
            if self.m == 1:
                return "M"
            if self.m == -1:
                return "-M"
            return f"{self.m}M"

        if self.m == 1:
            return f"M + {self.b}"
        if self.m == -1:
            return f"-M + {self.b}"

        sign = "+" if self.b > 0 else "-"
        return f"{self.m}M {sign} {abs(self.b)}"


def F(x):
    return Fraction(x)


def print_tableau(tableau, basis, cb, variables, iteration):
    print("\n" + "=" * 100)
    print(f"ITERATION {iteration}")
    print("=" * 100)

    header = ["Cb", "BV"] + variables + ["RHS"]
    print(" | ".join(f"{x:^12}" for x in header))
    print("-" * 100)

    for i in range(len(tableau)):
        row = [str(cb[i]), basis[i]]

        for x in tableau[i]:
            row.append(str(x))

        print(" | ".join(f"{x:^12}" for x in row))


def choose_entering(reduced_costs):
    positive = [i for i, x in enumerate(reduced_costs) if x.is_positive()]

    if not positive:
        return None

    # Big-M priority:
    # larger M coefficient first, then larger constant
    return max(
        positive,
        key=lambda i: (reduced_costs[i].m, reduced_costs[i].b)
    )


def big_m_simplex(c, A, signs, b, maximize=True):
    if not maximize:
        c = [-x for x in c]

    m = len(A)
    n = len(c)

    variables = [f"x{i+1}" for i in range(n)]
    cost = [Term(0, x) for x in c]

    rows = []
    artificial = []

    # Convert RHS to positive
    for i in range(m):
        row = list(map(F, A[i]))
        rhs = F(b[i])
        sign = signs[i]

        if rhs < 0:
            row = [-x for x in row]
            rhs = -rhs

            if sign == "<=":
                sign = ">="
            elif sign == ">=":
                sign = "<="

        rows.append([row, sign, rhs])

    # Add slack / surplus / artificial variables
    for i in range(m):
        row, sign, rhs = rows[i]

        for old_row, _, _ in rows:
            pass

    # Build variable columns dynamically
    final_rows = []
    cb = []
    basis = []

    for i in range(m):
        row, sign, rhs = rows[i]

        final_rows.append({
            "coeff": row[:],
            "rhs": rhs,
            "sign": sign
        })

    # Add variable columns
    extra_names = []
    extra_costs = []

    for i in range(m):
        sign = final_rows[i]["sign"]

        if sign == "<=":
            name = f"s{i+1}"
            extra_names.append(name)
            extra_costs.append(Term(0, 0))

        elif sign == ">=":
            name = f"s{i+1}"
            extra_names.append(name)
            extra_costs.append(Term(0, 0))

            name2 = f"A{i+1}"
            extra_names.append(name2)
            extra_costs.append(Term(-1, 0))
            artificial.append(name2)

        else:
            name = f"A{i+1}"
            extra_names.append(name)
            extra_costs.append(Term(-1, 0))
            artificial.append(name)

    variables += extra_names
    cost += extra_costs

    total_vars = len(variables)

    # Build coefficient matrix
    matrix = []

    extra_index = 0

    for i in range(m):
        original = final_rows[i]["coeff"]
        sign = final_rows[i]["sign"]

        row = [F(x) for x in original]

        if sign == "<=":
            # slack
            for j in range(len(extra_names)):
                row.append(F(0))

            idx = variables.index(f"s{i+1}")
            row[idx] = F(1)

            basis.append(f"s{i+1}")
            cb.append(Term(0, 0))

        elif sign == ">=":
            for j in range(len(extra_names)):
                row.append(F(0))

            idx_s = variables.index(f"s{i+1}")
            idx_a = variables.index(f"A{i+1}")

            row[idx_s] = F(-1)
            row[idx_a] = F(1)

            basis.append(f"A{i+1}")
            cb.append(Term(-1, 0))

        else:
            for j in range(len(extra_names)):
                row.append(F(0))

            idx_a = variables.index(f"A{i+1}")
            row[idx_a] = F(1)

            basis.append(f"A{i+1}")
            cb.append(Term(-1, 0))

        matrix.append(row + [final_rows[i]["rhs"]])

    # Convert numerical entries into Term
    tableau = []

    for row in matrix:
        tableau.append([Term(0, x) for x in row[:-1]])

    rhs = [row[-1] for row in matrix]

    # Make artificial costs -M
    for i, name in enumerate(basis):
        if name in artificial:
            cb[i] = Term(-1, 0)

    # Print initial tableau
    def calculate_z():
        zj = []

        for j in range(total_vars):
            value = Term()

            for i in range(m):
                value = value + tableau[i][j] * cb[i]

            zj.append(value)

        zrhs = Term()

        for i in range(m):
            zrhs = zrhs + Term(0, rhs[i]) * cb[i]

        return zj, zrhs

    iteration = 0

    while True:
        iteration += 1

        print("\n")
        print_tableau(
            [row[:] + [rhs[i]] for i, row in enumerate(tableau)],
            basis,
            cb,
            variables,
            iteration
        )

        zj, z_value = calculate_z()

        reduced = []

        for j in range(total_vars):
            reduced.append(cost[j] - zj[j])

        print("\nZj:")
        print([str(x) for x in zj])

        print("\nCj - Zj:")
        print([str(x) for x in reduced])

        entering = choose_entering(reduced)

        if entering is None:
            break

        print(f"\nEntering variable: {variables[entering]}")

        # Ratio test
        ratios = []

        for i in range(m):
            pivot_coeff = tableau[i][entering]

            if pivot_coeff.b > 0 and pivot_coeff.m == 0:
                ratio = rhs[i] / pivot_coeff.b
                ratios.append((ratio, i))
            else:
                ratios.append((None, i))

        valid = [x for x in ratios if x[0] is not None]

        if not valid:
            print("Problem is unbounded.")
            return

        leaving_ratio, leaving = min(valid, key=lambda x: x[0])

        print(f"Leaving variable: {basis[leaving]}")
        print(f"Pivot element: {tableau[leaving][entering]}")

        pivot = tableau[leaving][entering]

        # Normalize pivot row
        for j in range(total_vars):
            tableau[leaving][j] = tableau[leaving][j] / pivot

        rhs[leaving] = rhs[leaving] / pivot

        # Eliminate entering column
        for i in range(m):
            if i == leaving:
                continue

            factor = tableau[i][entering]

            if not factor.is_zero():
                for j in range(total_vars):
                    tableau[i][j] = (
                        tableau[i][j] - tableau[leaving][j] * factor
                    )

                rhs[i] = rhs[i] - rhs[leaving] * factor

        basis[leaving] = variables[entering]
        cb[leaving] = cost[entering]

    # Final solution
    print("\n" + "=" * 100)
    print("OPTIMAL SOLUTION")
    print("=" * 100)

    solution = {v: Fraction(0) for v in variables}

    for i in range(m):
        if basis[i] in solution:
            solution[basis[i]] = rhs[i]

    # Check artificial variables
    for a in artificial:
        if solution[a] > 0:
            print("Infeasible solution: artificial variable remains positive.")
            return

    print("\nVariable values:")

    for v in variables[:n]:
        print(f"{v} = {solution[v]}")

    final_z = Term()

    for i in range(m):
        final_z = final_z + cb[i] * rhs[i]

    if not maximize:
        final_z = -final_z

    print(f"\nOptimal objective value = {final_z}")


if __name__ == "__main__":

    # CASE STUDY
    # Production Planning Problem

    c = [50, 40, 45, 30]

    A = [
        [1, 1, 1, 1],
        [2, 1, 3, 1],
        [1, 2, 1, 2],
        [3, 1, 2, 1]
    ]

    signs = ["<=", ">=", "=", "<="]

    b = [80, 60, 70, 100]

    big_m_simplex(
        c,
        A,
        signs,
        b,
        maximize=True
    )
