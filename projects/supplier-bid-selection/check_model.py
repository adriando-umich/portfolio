"""Supplier bid selection. Check of the Excel Solver model by full enumeration (4,096 plans)."""
from itertools import product

SUPPLIER = [1, 2, 3, 1, 4, 2, 5, 6, 3, 7, 2, 5]
PRICE = [2050, 350, 1199, 220, 4639, 199, 1199, 1350, 350, 2200, 999, 1700]
IN_BID = [  # item x bid
    [1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0], [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0], [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0], [0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1],
    [0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1]]


def count(x, supplier):
    return sum(v for v, s in zip(x, SUPPLIER) if s == supplier)


def spend(x, supplier):
    return sum(p * v for p, v, s in zip(PRICE, x, SUPPLIER) if s == supplier)


def best_plan(policy=lambda x: True, need=None):
    need = need or [1] * 12
    best = None
    for x in product([0, 1], repeat=12):
        covered = all(sum(a * v for a, v in zip(row, x)) >= n for row, n in zip(IN_BID, need))
        if covered and policy(x):
            cost = sum(p * v for p, v in zip(PRICE, x))
            if best is None or cost < best[0]:
                best = (cost, [b + 1 for b in range(12) if x[b]])
    return best


if __name__ == "__main__":
    print("No policy:", best_plan())
    print("Second source for item 5:", best_plan(need=[1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1]))
    print("Local supplier (6 or 7):", best_plan(lambda x: count(x, 6) + count(x, 7) >= 1))
    print("Strategic partners:", best_plan(lambda x: count(x, 1) >= 1 and count(x, 3) >= 1 and count(x, 5) >= 2))
    print("Minimum order, supplier 1:", best_plan(lambda x: spend(x, 1) == 0 or spend(x, 1) >= 500))
