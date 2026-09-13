from fractions import Fraction


class Term:
    # Represents a*M + b
    def __init__(self, m=0, b=0):
        self.m = Fraction(m)
        self.b = Fraction(b)

    def __add__(self, other):
        other = to_term(other)
        return Term(self.m + other.m, self.b + other.b)

    __radd__ = __add__

    def __sub__(self, other):
        other = to_term(other)
        return Term(self.m - other.m, self.b - other.b)

    def __rsub__(self, other):
        return to_term(other) - self

    def __neg__(self):
        return Term(-self.m, -self.b)

    def __mul__(self, other):
        if isinstance(other, Term):
            if other.m != 0:
                raise ValueError("Cannot multiply two M terms.")
            other = other.b

        other = Fraction(other)
        return Term(self.m * other, self.b * other)

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = Fraction(other)
        return Term(self.m / other, self.b / other)

    def is_positive(self):
        return self.m > 0 or (self.m == 0 and self.b > 0)

    def is_negative(self):
        return self.m < 0 or (self.m == 0 and self.b < 0)

    def is_zero(self):
        return self.m == 0 and self.b == 0

    def __str__(self):
        if self.m != 0 and self.b != 0:
            if self.b > 0:
                return f"{self.m}M + {self.b}"
            return f"{self.m}M - {abs(self.b)}"

        if self.m != 0:
            return f"{self.m}M"

        return str(self.b)


def to_term(x):
    if isinstance(x, Term):
        return x
    return Term(0, x)


def fmt(x):
    if isinstance(x, Term):
        return str(x)
    return str(Fraction(x))


def print_tableau(tableau, basis, cb, columns, iteration):
    print("\n" + "=" * 120)
    print(f"ITERATION {iteration}")
    print("=" * 120)

    headers = ["Cb", "BV"] + columns + ["RHS"]

    print(" | ".join(f"{h:^12}" for h in headers))
    print("-" * 120)

    for i in range(len(tableau)):
        values = [fmt(cb[i]), basis[i]]

        for j in range(len(columns)):
            values.append(fmt(tableau[i][j]))

        values.append(fmt(tableau[i][-1]))

        print(" | ".join(f"{v:^12}" for v in values))


def big_m_simplex(A, b, signs, c):
    A = [[Fraction(x) for x in row] for row in A]
    b = [Fraction(x) for x in b]
    c = [Fraction(x) for x in c]

    m = len(A)
    n = len(c)

    columns = [f"x{i + 1}" for i in range(n)]

    tableau = [row[:] + [b[i]] for i, row in enumerate(A)]

    basis = [None] * m
    cb = [Term(0) for _ in range(m)]

    slack_count = 0
    surplus_count = 0
    artificial_count = 0

    # Add slack, surplus and artificial variables
    for i in range(m):

        if signs[i] == "<=":
            slack_count += 1
            name = f"s{slack_count}"

            for row in tableau:
                row.insert(-1, Fraction(0))

            tableau[i][-2] = Fraction(1)
            columns.append(name)

            basis[i] = name
            cb[i] = Term(0)

        elif signs[i] == ">=":
            surplus_count += 1
            surplus_name = f"e{surplus_count}"

            for row in tableau:
                row.insert(-1, Fraction(0))

            tableau[i][-2] = Fraction(-1)
            columns.append(surplus_name)

            artificial_count += 1
            artificial_name = f"A{artificial_count}"

            for row in tableau:
                row.insert(-1, Fraction(0))

            tableau[i][-2] = Fraction(1)
            columns.append(artificial_name)

            basis[i] = artificial_name
            cb[i] = Term(-1, 0)

        elif signs[i] == "=":
            artificial_count += 1
            artificial_name = f"A{artificial_count}"

            for row in tableau:
                row.insert(-1, Fraction(0))

            tableau[i][-2] = Fraction(1)
            columns.append(artificial_name)

            basis[i] = artificial_name
            cb[i] = Term(-1, 0)

        else:
            raise ValueError("Constraint must be <=, >= or =")

    # Objective coefficients
    cj = []

    for value in c:
        cj.append(Term(0, value))

    for name in columns[n:]:
        if name.startswith("A"):
            cj.append(Term(-1, 0))
        else:
            cj.append(Term(0, 0))

    for i in range(m):
        cb[i] = next(
            cj[j] for j in range(len(columns))
            if columns[j] == basis[i]
        )

    iteration = 1

    while True:

        print_tableau(
            tableau,
            basis,
            cb,
            columns,
            iteration
        )

        # Calculate Zj
        zj = []

        for j in range(len(columns)):
            value = Term(0, 0)

            for i in range(m):
                value += cb[i] * tableau[i][j]

            zj.append(value)

        # Calculate Z
        z_value = Term(0, 0)

        for i in range(m):
            z_value += cb[i] * tableau[i][-1]

        # Calculate Cj - Zj
        reduced = []

        for j in range(len(columns)):
            reduced.append(cj[j] - zj[j])

        print("\nCj - Zj:")
        for j in range(len(columns)):
            print(f"{columns[j]} = {fmt(reduced[j])}", end="   ")

        print("\n")

        # Choose entering variable
        entering = None

        for j in range(len(columns)):

            if reduced[j].is_positive():

                if entering is None:
                    entering = j

                else:
                    current = reduced[entering]
                    candidate = reduced[j]

                    if candidate.m > current.m:
                        entering = j

                    elif (
                        candidate.m == current.m
                        and candidate.b > current.b
                    ):
                        entering = j

        # Optimality condition
        if entering is None:
            print("\n" + "=" * 120)
            print("OPTIMAL SOLUTION")
            print("=" * 120)

            solution = {}

            for name in columns:
                solution[name] = Fraction(0)

            for i in range(m):
                solution[basis[i]] = tableau[i][-1]

            # Check artificial variables
            for i in range(m):
                if basis[i].startswith("A") and tableau[i][-1] > 0:
                    print("\nProblem is INFEASIBLE.")
                    return

            print("\nDecision Variables:")

            for i in range(n):
                print(
                    f"x{i + 1} = "
                    f"{solution[f'x{i + 1}']}"
                )

            print(f"\nMaximum Z = {z_value}")

            if z_value.b.denominator == 1:
                print(f"Maximum Z = {z_value.b}")

            else:
                print(
                    f"Maximum Z = "
                    f"{float(z_value.b):.2f}"
                )

            return

        entering_name = columns[entering]

        print(
            f"\nEntering variable = {entering_name}"
        )

        # Ratio test
        ratios = []

        for i in range(m):

            coefficient = tableau[i][entering]

            if coefficient > 0:

                ratio = tableau[i][-1] / coefficient

                if ratio >= 0:
                    ratios.append((ratio, i))

        if not ratios:
            print("\nProblem is UNBOUNDED.")
            return

        ratio, leaving = min(
            ratios,
            key=lambda x: (x[0], x[1])
        )

        print(
            f"Leaving variable = {basis[leaving]}"
        )

        print(f"Minimum ratio = {ratio}")

        # Pivot
        pivot = tableau[leaving][entering]

        for j in range(len(columns) + 1):
            tableau[leaving][j] /= pivot

        # Make entering column zero in all other rows
        for i in range(m):

            if i != leaving:

                factor = tableau[i][entering]

                if factor != 0:

                    for j in range(len(columns) + 1):
                        tableau[i][j] -= (
                            factor * tableau[leaving][j]
                        )

        basis[leaving] = entering_name
        cb[leaving] = cj[entering]

        iteration += 1

        if iteration > 50:
            print("\nToo many iterations.")
            return


# ============================================================
# CASE STUDY
# Production Planning Problem
# ============================================================

A = [
    [1, 1, 1, 1],
    [2, 1, 3, 1],
    [1, 2, 1, 2],
    [3, 1, 2, 1]
]

b = [
    80,
    60,
    70,
    100
]

signs = [
    "<=",
    ">=",
    "=",
    "<="
]

c = [
    50,
    40,
    45,
    30
]


big_m_simplex(A, b, signs, c)
