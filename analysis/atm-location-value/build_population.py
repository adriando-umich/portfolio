"""Case 04: residents near each ATM location, from 2020 Census tracts.

Run: python3 build_population.py <atm_sites_dmv.csv> <folder with tracts_11/24/51.json> <output folder>
Source of the tract files: TIGERweb, service tigerWMS_Census2020, layer 6 (Census Tracts),
fields GEOID, CENTLAT, CENTLON, POP100. One file for each state (DC 11, MD 24, VA 51).
Outputs: atm_population_dmv.csv, atm_coverage_sets_dmv.csv, and two totals for model.py.
"""
import csv
import json
import math
import sys


def miles(a, b, c, d):
    r, t = 3958.8, math.radians
    h = math.sin(t(c - a) / 2) ** 2 + math.cos(t(a)) * math.cos(t(c)) * math.sin(t(d - b) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def main(sites, raw, out):
    S = list(csv.DictReader(open(sites, newline=""), delimiter="|"))
    for s in S:
        s["lat"], s["lon"], s["dep"] = float(s["lat"]), float(s["lon"]), s["co_deposit"] == "1"
    tracts = []
    for st in ("11", "24", "51"):
        for f in json.load(open(f"{raw}/tracts_{st}.json"))["features"]:
            a = f["attributes"]
            if a["POP100"]:
                tracts.append((float(a["CENTLAT"]), float(a["CENTLON"]), int(a["POP100"])))
    res = {s["id"]: dict(p1=0, p2=0, p3=0, c5=0, ex2=0) for s in S}
    sets, footprint, covered = {}, 0, 0
    for lat, lon, pop in tracts:
        d = [miles(lat, lon, s["lat"], s["lon"]) for s in S]
        m = min(d)
        if m > 5:
            continue  # outside the footprint: no Capital One ATM in 5 miles
        footprint += pop
        res[S[d.index(m)]["id"]]["c5"] += pop
        dep = []
        for s, x in zip(S, d):
            for k, lim in (("p1", 1), ("p2", 2), ("p3", 3)):
                if x <= lim:
                    res[s["id"]][k] += pop
            if x <= 2 and s["dep"]:
                dep.append(s["id"])
        if dep:
            covered += pop
            key = "+".join(sorted(dep))
            sets[key] = sets.get(key, 0) + pop
            if len(dep) == 1:
                res[dep[0]]["ex2"] += pop
    with open(f"{out}/atm_population_dmv.csv", "w") as f:
        f.write("id|pop_1mi|pop_2mi|pop_3mi|catchment_5mi|exclusive_deposit_2mi\n")
        for s in S:
            r = res[s["id"]]
            f.write(f"{s['id']}|{r['p1']}|{r['p2']}|{r['p3']}|{r['c5']}|{r['ex2']}\n")
    with open(f"{out}/atm_coverage_sets_dmv.csv", "w") as f:
        for k in sorted(sets):
            f.write(f"{k}|{sets[k]}\n")
    print("tracts in footprint:", sum(1 for t in tracts if min(
        miles(t[0], t[1], s["lat"], s["lon"]) for s in S) <= 5))
    print("FOOTPRINT =", footprint, " COVERED =", covered)


if __name__ == "__main__":
    main(*sys.argv[1:4])
