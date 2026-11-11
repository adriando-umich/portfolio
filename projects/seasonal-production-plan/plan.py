"""Seasonal production plan: integer program for workforce, overtime and inventory over 12 months."""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

DEMAND = [4400, 4400, 6000, 8000, 6600, 11800, 13000, 11200, 10800, 7600, 6000, 5600]
SALARY, HIRE, FIRE, OT, HOLD, PER, CAP, W0, I0 = 2400, 1800, 1200, 3300, 8, 40, 13000, 160, 240


def plan(mode="mixed", whole=True):
    """Variables for each month: hires, layoffs, workers on overtime, workers, inventory. All integers."""
    T = 12; n = 5 * T; h, f, o, w, inv = (lambda k: (lambda t: k * T + t))(0), None, None, None, None
    ix = lambda k, t: k * T + t
    c = np.zeros(n)
    for t in range(T): c[ix(0, t)], c[ix(1, t)], c[ix(2, t)], c[ix(3, t)], c[ix(4, t)] = HIRE, FIRE, OT, SALARY, HOLD
    A, lo, hi = [], [], []
    def row(coefs, l, u):
        r = np.zeros(n)
        for k, v in coefs.items(): r[k] += v
        A.append(r); lo.append(l); hi.append(u)
    for t in range(T):
        row({ix(3, t): 1, ix(0, t): -1, ix(1, t): 1, **({ix(3, t - 1): -1} if t else {})}, W0 if t == 0 else 0, W0 if t == 0 else 0)                 # workers
        row({ix(4, t): 1, ix(3, t): -PER, ix(2, t): -PER, **({ix(4, t - 1): -1} if t else {})}, (I0 if t == 0 else 0) - DEMAND[t], (I0 if t == 0 else 0) - DEMAND[t])  # inventory
        row({ix(3, t): PER, ix(2, t): PER}, 0, CAP)        # plant capacity
        row({ix(2, t): 1, ix(3, t): -1}, -np.inf, 0)       # one overtime shift per worker
    ub = np.full(n, np.inf)
    if mode == "level":                                     # one workforce size all year, no overtime
        for t in range(T):
            ub[ix(2, t)] = 0; ub[ix(1, t)] = 0
            if t: ub[ix(0, t)] = 0
    if mode == "chase":                                     # production follows demand; no planned inventory
        for t in range(T): ub[ix(4, t)] = PER - 1
    r = milp(c, constraints=LinearConstraint(np.array(A), lo, hi), integrality=np.ones(n) * whole, bounds=Bounds(0, ub), options={"mip_rel_gap": 0})
    x = (np.round(r.x).astype(int) if whole else r.x).reshape(5, T)
    parts = {"Salaries": SALARY * x[3].sum(), "Hires": HIRE * x[0].sum(), "Layoffs": FIRE * x[1].sum(), "Overtime": OT * x[2].sum(), "Inventory": HOLD * x[4].sum()}
    return round(r.fun), x, parts


if __name__ == "__main__":
    for mode in ("mixed", "level", "chase"):
        cost, x, parts = plan(mode)
        print(mode, cost, {k: int(v) for k, v in parts.items()})
        print("  workers", [int(v) for v in x[3]])
