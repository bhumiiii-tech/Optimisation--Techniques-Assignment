from fractions import Fraction


class Term:
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

    def __mul__(self, other):
        if isinstance(other, Term):
            if other.m != 0:
                raise ValueError("Cannot multiply two M terms.")
            other = other.b

        other = Fraction(other)
        return Term(self.m * other, self.b * other)

    __rmul__ = __mul__

    def positive(self):
        return self.m > 0 or (self.m == 0 and self.b > 0)

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


def print_table(table, basis, cb, columns, iteration):

    print("\n" + "=" * 100)
    print(f"ITERATION {iteration}")
    print("=" * 100)

    headers = ["Cb", "BV"] + columns + ["RHS"]

    print(" | ".join(f"{h:^10}" for h in headers))
    print("-" * 100)

    for i in range(len(table)):

        row = [str(cb[i]), basis[i]]

        for j in range(len(columns)):
            row.append(str(table[i][j]))

        row.append(str(table[i][-1]))

        print(" | ".join(f"{x:^10}" for x in row))


def big_m_simplex():

    # ========================================================
    # PROBLEM DATA
    # ========================================================

    c = [20, 6, 12]

    A = [
        [3, 1, 1],
        [4, 4, 2],
        [4, 1, 2]
    ]

    b = [45, 41, 15]

    signs = ["<=", "=", "="]

    # ========================================================
    # PRINT PROBLEM
    # ========================================================

    print("\n" + "=" * 100)
    print("BIG-M SIMPLEX METHOD")
    print("=" * 100)

    print("\nProblem Formulation:")

    print("\nMaximize")
    print("Z = 20x1 + 6x2 + 12x3")

    print("\nSubject to:")
    print("3x1 + x2 + x3 <= 45")
    print("4x1 + 4x2 + 2x3 = 41")
    print("4x1 + x2 + 2x3 = 15")

    print("\nx1, x2, x3 >= 0")

    # ========================================================
    # STANDARD FORM
    # ========================================================

    print("\nStandard Form:")

    print("3x1 + x2 + x3 + s1 = 45")
    print("4x1 + 4x2 + 2x3 + A1 = 41")
    print("4x1 + x2 + 2x3 + A2 = 15")

    print("\nObjective Function:")
    print("Maximize Z = 20x1 + 6x2 + 12x3 - M A1 - M A2")

    # ========================================================
    # INITIAL TABLEAU
    # ========================================================

    columns = [
        "x1", "x2", "x3",
        "s1", "A1", "A2"
    ]

    cj = [
        Term(0, 20),
        Term(0, 6),
        Term(0, 12),
        Term(0, 0),
        Term(-1, 0),
        Term(-1, 0)
    ]

    table = [
        [
            Fraction(3),
            Fraction(1),
            Fraction(1),
            Fraction(1),
            Fraction(0),
            Fraction(0),
            Fraction(45)
        ],

        [
            Fraction(4),
            Fraction(4),
            Fraction(2),
            Fraction(0),
            Fraction(1),
            Fraction(0),
            Fraction(41)
        ],

        [
            Fraction(4),
            Fraction(1),
            Fraction(2),
            Fraction(0),
            Fraction(0),
            Fraction(1),
            Fraction(15)
        ]
    ]

    basis = ["s1", "A1", "A2"]

    cb = [
        Term(0, 0),
        Term(-1, 0),
        Term(-1, 0)
    ]

    iteration = 1

    # ========================================================
    # SIMPLEX ITERATIONS
    # ========================================================

    while True:

        print_table(
            table,
            basis,
            cb,
            columns,
            iteration
        )

        # ----------------------------------------------------
        # Calculate Zj
        # ----------------------------------------------------

        zj = []

        for j in range(len(columns)):

            value = Term(0)

            for i in range(len(table)):
                value += cb[i] * table[i][j]

            zj.append(value)

        # ----------------------------------------------------
        # Calculate Z
        # ----------------------------------------------------

        z = Term(0)

        for i in range(len(table)):
            z += cb[i] * table[i][-1]

        # ----------------------------------------------------
        # Calculate Cj - Zj
        # ----------------------------------------------------

        reduced = []

        for j in range(len(columns)):
            reduced.append(cj[j] - zj[j])

        print("\nCj - Zj:")

        for j in range(len(columns)):

            print(
                f"{columns[j]} = {reduced[j]}",
                end="   "
            )

        # ----------------------------------------------------
        # Find entering variable
        # ----------------------------------------------------

        entering = None

        for j in range(len(columns)):

            if reduced[j].positive():

                if entering is None:
                    entering = j

                elif reduced[j].m > reduced[entering].m:
                    entering = j

                elif (
                    reduced[j].m == reduced[entering].m
                    and reduced[j].b > reduced[entering].b
                ):
                    entering = j

        # ----------------------------------------------------
        # Optimality
        # ----------------------------------------------------

        if entering is None:

            print("\n\n" + "=" * 100)
            print("OPTIMAL SOLUTION")
            print("=" * 100)

            solution = {
                "x1": Fraction(0),
                "x2": Fraction(0),
                "x3": Fraction(0)
            }

            for i in range(len(table)):

                if basis[i] in solution:
                    solution[basis[i]] = table[i][-1]

            print("\nx1 =", solution["x1"])
            print("x2 =", solution["x2"])
            print("x3 =", solution["x3"])

            print("\nMaximum Z =", z)
            print(
                "Maximum Z =",
                float(z.b)
            )

            break

        entering_name = columns[entering]

        print(
            "\n\nEntering variable =",
            entering_name
        )

        # ----------------------------------------------------
        # Ratio Test
        # ----------------------------------------------------

        ratios = []

        for i in range(len(table)):

            if table[i][entering] > 0:

                ratio = (
                    table[i][-1]
                    / table[i][entering]
                )

                if ratio >= 0:
                    ratios.append((ratio, i))

        if not ratios:

            print("\nProblem is UNBOUNDED.")
            break

        ratio, leaving = min(
            ratios,
            key=lambda x: (x[0], x[1])
        )

        print(
            "Leaving variable =",
            basis[leaving]
        )

        # ----------------------------------------------------
        # Pivot Operation
        # ----------------------------------------------------

        pivot = table[leaving][entering]

        for j in range(len(columns) + 1):
            table[leaving][j] /= pivot

        for i in range(len(table)):

            if i != leaving:

                factor = table[i][entering]

                if factor != 0:

                    for j in range(len(columns) + 1):

                        table[i][j] -= (
                            factor
                            * table[leaving][j]
                        )

        basis[leaving] = entering_name
        cb[leaving] = cj[entering]

        iteration += 1


# ============================================================
# RUN
# ============================================================

big_m_simplex()
