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


def print_tableau(table, basis, cb, columns, iteration):

    print("\n" + "=" * 100)
    print("ITERATION", iteration)
    print("=" * 100)

    print("Cb | BV |", " | ".join(columns), "| RHS")
    print("-" * 100)

    for i in range(len(table)):

        row = [str(cb[i]), basis[i]]

        for j in range(len(columns)):
            row.append(str(table[i][j]))

        row.append(str(table[i][-1]))

        print(" | ".join(f"{x:^10}" for x in row))


def big_m_simplex(A, b, signs, c):

    A = [[Fraction(x) for x in row] for row in A]
    b = [Fraction(x) for x in b]
    c = [Fraction(x) for x in c]

    m = len(A)
    n = len(c)

    columns = [f"x{i+1}" for i in range(n)]
    table = [A[i][:] + [b[i]] for i in range(m)]

    basis = [None] * m
    slack = 0
    artificial = 0

    for i in range(m):

        if signs[i] == "<=":

            slack += 1
            name = f"s{slack}"

            for row in table:
                row.insert(-1, Fraction(0))

            table[i][-2] = 1
            columns.append(name)
            basis[i] = name

        elif signs[i] == "=":

            artificial += 1
            name = f"A{artificial}"

            for row in table:
                row.insert(-1, Fraction(0))

            table[i][-2] = 1
            columns.append(name)
            basis[i] = name

    cj = [Term(0, x) for x in c]

    for name in columns[n:]:

        if name.startswith("A"):
            cj.append(Term(-1, 0))
        else:
            cj.append(Term(0, 0))

    cb = []

    for name in basis:

        for j in range(len(columns)):

            if columns[j] == name:
                cb.append(cj[j])
                break

    iteration = 1

    while True:

        print_tableau(
            table,
            basis,
            cb,
            columns,
            iteration
        )

        zj = []

        for j in range(len(columns)):

            value = Term(0)

            for i in range(m):
                value += cb[i] * table[i][j]

            zj.append(value)

        z = Term(0)

        for i in range(m):
            z += cb[i] * table[i][-1]

        reduced = [
            cj[j] - zj[j]
            for j in range(len(columns))
        ]

        print("\nCj - Zj:")

        for j in range(len(columns)):
            print(
                f"{columns[j]} = {reduced[j]}",
                end="   "
            )

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

        if entering is None:

            print("\n\n" + "=" * 100)
            print("OPTIMAL SOLUTION")
            print("=" * 100)

            solution = {
                name: Fraction(0)
                for name in columns
            }

            for i in range(m):
                solution[basis[i]] = table[i][-1]

            print("\nDecision Variables:")

            for i in range(n):
                print(
                    f"x{i+1} = "
                    f"{solution[f'x{i+1}']}"
                )

            print(f"\nMaximum Z = {z}")
            print(f"Maximum Z = {float(z.b):.2f}")

            return

        entering_name = columns[entering]

        print(
            f"\n\nEntering variable = "
            f"{entering_name}"
        )

        ratios = []

        for i in range(m):

            if table[i][entering] > 0:

                ratio = (
                    table[i][-1]
                    / table[i][entering]
                )

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
            f"Leaving variable = "
            f"{basis[leaving]}"
        )

        pivot = table[leaving][entering]

        for j in range(len(columns) + 1):
            table[leaving][j] /= pivot

        for i in range(m):

            if i != leaving:

                factor = table[i][entering]

                for j in range(len(columns) + 1):
                    table[i][j] -= (
                        factor * table[leaving][j]
                    )

        basis[leaving] = entering_name
        cb[leaving] = cj[entering]

        iteration += 1


# ============================================================
# CASE STUDY
# ============================================================

A = [
    [3, 1, 1],
    [4, 4, 2],
    [4, 1, 2]
]

b = [
    45,
    41,
    15
]

signs = [
    "<=",
    "=",
    "="
]

c = [
    20,
    6,
    12
]

big_m_simplex(A, b, signs, c)
