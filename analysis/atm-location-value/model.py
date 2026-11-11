"""Case 04: value of the owned ATM at each of 75 locations.

Run: python3 model.py <atm_sites_dmv.csv> <atm_population_dmv.csv> <atm_coverage_sets_dmv.csv> <output folder>

Inputs:
- Location file from the Capital One location finder (11/11/2026).
- Population file: 2020 Census tract population near each location (TIGERweb).
- Coverage file: residents by the set of Capital One deposit ATMs in 2 miles of their tract.
- Assumptions (base, low, high). The technical document on the site gives the source of each value.
Only the Python standard library is necessary.
"""
import csv
import json
import sys
from itertools import product

A = {
    "A1_fee": (3.00, 3.00, 3.00),
    "A3_trend": (-0.032, -0.07, 0.0),
    "A4_tx_branch": (2600, 1300, 3900),
    "A5_tx_standalone": (1200, 600, 1800),
    "A6_opex": (1800, 1200, 2400),
    "A7_partner_cost": (0.60, 0.40, 1.00),
    "A8_rel_revenue": (850, 350, 1350),
    "A9_rel_cost": (325, 250, 400),
    "B1_deposit_share": (0.15, 0.05, 0.25),
    "B2_noncustomer_share": (0.20, 0.10, 0.40),
    "B3_deposits_per_customer": (2, 1, 4),
    "B4_leave_share": (0.10, 0.02, 0.25),
    "B5_rent": (500, 250, 1000),
    "B6_years": (5, 3, 7),
    "B7_discount": (0.10, 0.08, 0.12),
}
BASE = {k: v[0] for k, v in A.items()}
SUBSTITUTE_MILES = 2.0
# Volume index = residents in 2 miles / mean of the same type, limited to 0.5-1.5.
INDEX_MIN, INDEX_MAX = 0.5, 1.5
FOOTPRINT = 6220710      # residents in 5 miles of a Capital One ATM (2020 Census)
COVERED = 3283769        # of these, residents in 2 miles of a Capital One deposit ATM
COVERAGE_LIMIT = 0.01    # rule set before the analysis: decrease of 1 point or less


COVER = []  # (set of location ids, residents)


def coverage_loss(ids):
    """Residents who lose all Capital One deposit ATMs in 2 miles if these ids are removed."""
    ids = set(ids)
    return sum(n for s, n in COVER if s <= ids)


def load(sites, pops):
    pop = {r["id"]: r for r in csv.DictReader(open(pops, newline=""), delimiter="|")}
    rows = []
    for r in csv.DictReader(open(sites, newline=""), delimiter="|"):
        def num(k):
            return float(r[k]) if r[k] else None
        co, pd_ = num("co_deposit_nearest_mi"), num("partner_deposit_nearest_mi")
        r["standalone"] = r["site_type"] == "standalone"
        r["deposit"] = r["co_deposit"] == "1"
        r["no_substitute"] = r["deposit"] and co > SUBSTITUTE_MILES and (
            pd_ is None or pd_ > SUBSTITUTE_MILES)
        r["pop2"] = int(pop[r["id"]]["pop_2mi"])
        r["exclusive"] = int(pop[r["id"]]["exclusive_deposit_2mi"]) if r["deposit"] else 0
        rows.append(r)
    for group in (True, False):
        g = [r for r in rows if r["standalone"] == group]
        mean = sum(r["pop2"] for r in g) / len(g)
        for r in g:
            r["index"] = min(INDEX_MAX, max(INDEX_MIN, r["pop2"] / mean))
    return rows


def annuity(p):
    n, d, g = int(p["B6_years"]), p["B7_discount"], p["A3_trend"]
    trend = sum((1 + g) ** (t - 1) / (1 + d) ** t for t in range(1, n + 1))
    flat = sum(1 / (1 + d) ** t for t in range(1, n + 1))
    return trend, flat


def value(r, p, rel_factor=1.0, vol_factor=1.0):
    base_tx = p["A5_tx_standalone"] if r["standalone"] else p["A4_tx_branch"]
    tx = base_tx * r["index"] * vol_factor
    dep_tx = tx * p["B1_deposit_share"] if r["deposit"] else 0.0
    wd = tx - dep_tx  # all other transactions are treated as withdrawals
    fee = wd * p["B2_noncustomer_share"] * p["A1_fee"] * 12
    partner = wd * (1 - p["B2_noncustomer_share"]) * p["A7_partner_cost"] * 12
    profit = (p["A8_rel_revenue"] - p["A9_rel_cost"]) * rel_factor
    dep = (dep_tx / p["B3_deposits_per_customer"]) * p["B4_leave_share"] * profit \
        if r["no_substitute"] else 0.0
    rent = p["B5_rent"] * 12 if r["standalone"] else 0.0
    cost = p["A6_opex"] * 12 + rent
    trend, flat = annuity(p)
    return {"tx": tx, "fee": fee, "partner": partner, "deposit_value": dep, "cost": cost,
            "npv": (fee + partner + dep) * trend - cost * flat}


def network(rows, p, rel_factor=1.0, vol_factor=1.0):
    """Champion: keep all. Challenger: remove negative-NPV locations, worst first,
    while the coverage limit holds (exact loss from the coverage file)."""
    vals = [value(r, p, rel_factor, vol_factor) for r in rows]
    keep_all = sum(v["npv"] for v in vals)
    below = sorted((i for i, v in enumerate(vals) if v["npv"] < 0), key=lambda i: vals[i]["npv"])
    removed, protected, lost = [], [], 0
    for i in below:
        new = coverage_loss(rows[j]["id"] for j in removed + [i] if rows[j]["deposit"])
        if new <= COVERAGE_LIMIT * FOOTPRINT:
            removed.append(i)
            lost = new
        else:
            protected.append(i)
    rule = keep_all - sum(vals[i]["npv"] for i in removed)
    return {"vals": vals, "keep_all": keep_all, "rule": rule, "below": below,
            "removed": removed, "protected": protected, "lost": lost}


def break_even_tx(p, no_substitute, standalone):
    lo, hi = 0.0, 20000.0
    r = {"standalone": standalone, "deposit": True, "no_substitute": no_substitute, "index": 1.0}
    for _ in range(60):
        mid = (lo + hi) / 2
        q = dict(p, A4_tx_branch=mid, A5_tx_standalone=mid)
        lo, hi = (mid, hi) if value(r, q)["npv"] < 0 else (lo, mid)
    return round(hi)


def brief(n):
    return {"npv_keep_all": round(n["keep_all"]), "npv_rule": round(n["rule"]),
            "gain": round(n["rule"] - n["keep_all"]), "below_break_even": len(n["below"]),
            "removed": len(n["removed"]), "protected_by_coverage": len(n["protected"]),
            "coverage_loss_points": round(100 * n["lost"] / FOOTPRINT, 2)}


def main(sites, pops, cover, out):
    for line in open(cover):
        k, v = line.strip().split("|")
        COVER.append((set(k.split("+")), int(v)))
    assert sum(n for _, n in COVER) == COVERED
    rows = load(sites, pops)
    n = network(rows, BASE)
    vals = n["vals"]
    status = {i: "remove" for i in n["removed"]}
    status.update({i: "protect (coverage)" for i in n["protected"]})

    with open(f"{out}/results_by_location.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "city", "state", "site_type", "deposit", "no_substitute",
                    "pop_2mi", "exclusive_residents", "volume_index", "tx_month", "fee_income",
                    "partner_cost_avoided", "deposit_value", "cost", "npv_5y", "decision"])
        for i, (r, v) in enumerate(zip(rows, vals)):
            w.writerow([r["id"], r["name"], r["city"], r["state"], r["site_type"],
                        int(r["deposit"]), int(r["no_substitute"]), r["pop2"], r["exclusive"],
                        round(r["index"], 2), round(v["tx"]), round(v["fee"]),
                        round(v["partner"]), round(v["deposit_value"]), round(v["cost"]),
                        round(v["npv"]), status.get(i, "keep")])

    def types(idx):
        return {t: sum(rows[i]["site_type"] == t for i in idx)
                for t in ("branch", "cafe", "standalone")}

    s = {"locations": len(rows), "no_substitute": sum(r["no_substitute"] for r in rows),
         "base": brief(n), "below_by_type": types(n["below"]),
         "removed_by_type": types(n["removed"]),
         "removed": [rows[i]["name"] for i in n["removed"]],
         "protected": [rows[i]["name"] for i in n["protected"]],
         "below_and_no_substitute": sum(rows[i]["no_substitute"] for i in n["below"]),
         "coverage_base_share": round(COVERED / FOOTPRINT, 4),
         "value_split_year1": {k: round(sum(v[k] for v in vals))
                               for k in ("fee", "partner", "deposit_value", "cost")},
         "tx_month": {"min": round(min(v["tx"] for v in vals)),
                      "max": round(max(v["tx"] for v in vals))}}

    s["test_value"] = {name: dict(brief(network(rows, dict(BASE, A6_opex=A["A6_opex"][i]))),
                                  opex=A["A6_opex"][i])
                       for name, i in (("low", 1), ("base", 0), ("high", 2))}

    base_set = set(n["below"])
    s["test_stability"] = {}
    for f_ in (0.5, 1.5):
        m = network(rows, BASE, rel_factor=f_)
        ch = base_set ^ set(m["below"])
        s["test_stability"][str(f_)] = {"changed": len(ch), "share": round(len(ch) / len(rows), 3)}

    grid = [dict(B4=b4, B1=b1, A6=a6, **brief(network(
        rows, dict(BASE, B4_leave_share=b4, B1_deposit_share=b1, A6_opex=a6))))
        for b4, b1, a6 in product(A["B4_leave_share"], A["B1_deposit_share"], A["A6_opex"])]
    s["sensitivity_3_range_below"] = [min(g["below_break_even"] for g in grid),
                                      max(g["below_break_even"] for g in grid)]

    # Added after the first results: volume and non-customer share decide the answer.
    s["scenario_volume_x_noncustomer"] = {
        f"volume x{vf}": {f"noncustomer {int(b2 * 100)}%": len(network(
            rows, dict(BASE, B2_noncustomer_share=b2), vol_factor=vf)["below"])
            for b2 in (0.10, 0.20, 0.30, 0.40)}
        for vf in (0.5, 0.75, 1.0, 1.25, 1.5)}

    s["break_even_tx_month"] = {
        "branch_with_substitute": break_even_tx(BASE, False, False),
        "branch_no_substitute": break_even_tx(BASE, True, False),
        "standalone_with_substitute": break_even_tx(BASE, False, True),
        "standalone_no_substitute": break_even_tx(BASE, True, True)}

    with open(f"{out}/results_summary.json", "w") as f:
        json.dump(dict(s, sensitivity_3_grid=grid), f, indent=1)
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
