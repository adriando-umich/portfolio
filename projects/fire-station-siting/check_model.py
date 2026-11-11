"""Fire station siting. Check of the Excel Solver model by full enumeration (64 plans)."""
from itertools import product

TIME = [[3, 15, 21, 7, 15, 25], [11, 5, 13, 16, 12, 21], [21, 18, 2, 19, 13, 10],
        [8, 21, 20, 4, 8, 17], [14, 16, 12, 10, 3, 9], [22, 23, 9, 18, 8, 2]]  # region x site, minutes
COST = [400, 50, 300, 450, 250, 350]  # $ thousand


def best_plan(limit, rules=True):
    best = None
    for x in product([0, 1], repeat=6):
        covered = all(any(x[j] and TIME[i][j] <= limit for j in range(6)) for i in range(6))
        allowed = x[0] + x[5] <= 1 and x[3] <= x[0] and x[4] == x[5]
        if covered and (allowed or not rules):
            cost = sum(c * v for c, v in zip(COST, x))
            if best is None or cost < best[0]:
                best = (cost, [j + 1 for j in range(6) if x[j]])
    return best


if __name__ == "__main__":
    for limit in range(8, 26):
        print(limit, "min:", best_plan(limit) or "no plan covers all regions")
    print("12 min without the siting rules:", best_plan(12, rules=False))
