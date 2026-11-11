"""Page fragments, data entries and issue trees for three machine learning course projects. Run from the repo root."""
import json, os, shutil, sys
sys.path.insert(0, "tools")
from course_r import kpis, model, notes, bar, money
from course_trees import N
def load(s): return json.load(open(f"analysis/{s}/results.json"))
def out(slug, html):
    open(f"data/course/{slug}.html", "w", encoding="utf-8").write(html); os.makedirs(f"projects/{slug}", exist_ok=True); shutil.copy(f"analysis/{slug}/analysis.R", f"projects/{slug}/analysis.R")
E_ = {}
M = "Michigan Ross MBA"

def retention():
    slug = "employee-retention-targeting"; r = load(slug); ms = r["models"]; best = max(ms, key=lambda m: m["saving"]); base = ms[0]; n = r["test_rows"]
    top = max(m["saving"] for m in ms)
    rows = "".join(bar(f'<b>{m["model"]}</b>finds {m["recall"]:.0f}% of the leavers; {m["precision"]:.0f}% of the offers go to a leaver', max(m["saving"], 0) / top * 100, money(m["saving"]),
                       f'{m["flagged"]} offers', on=m is best, wide=True, neg=m["saving"] < 0) for m in sorted(ms, key=lambda m: -m["saving"]))
    rows += bar("<b>An offer to all employees</b>no model", 0, f"-${abs(r['offer_all']) / 1e6:.1f}M", f"{n:,} offers", wide=True, neg=True)
    G = sorted(r["groups"], key=lambda g: -g["rate"]); gt = max(g["rate"] for g in G)
    grows = "".join(bar(f'<b>{g["group"]}</b>{g["n"]:,} employees', g["rate"] / gt * 100, f'{g["rate"]:.0f}%', "leave", on=i == 0, wide=True) for i, g in enumerate(G))
    other = next(g for g in G if g["group"].startswith("All other")); risky = [g for g in G if g is not other]
    html = kpis([
        ("Saving from the retention offers", f'${best["saving"] / 1e6:.2f}M', f'for {n:,} test employees, against no program'),
        ("Employees who get an offer", f'{best["flagged"] / n * 100:.0f}%', f'those with a risk of {r["cutoff"] * 100:.0f}% or more; {best["precision"]:.0f}% of them are leavers'),
        ("Leavers that the offers reach", f'{best["recall"]:.0f}%', f'{best["leavers_found"]} of {r["test_leavers"]}'),
    ]) + f"""
<section class="part"><h2>A model that sees curves and combinations saves $2.6M; a straight-line model loses money</h2>
  <div class="cp-bars" role="img" aria-label="Saving of the retention program by model.">{rows}</div>
  <p class="cp-note">Assumptions: to replace an employee costs ${r["replace"]:,}. A retention offer costs ${r["offer"]:,} and keeps {r["keep"] * 100:.0f}% of the employees who would leave. An offer pays when the risk is above {r["cutoff"] * 100:.0f}%.</p>
</section>
<section class="part"><h2>Three groups hold almost all the leavers, and each has a different cause</h2>
  <div class="cp-bars" role="img" aria-label="Share of employees who leave, by group.">{grows}</div>
  <p class="cp-note">Low load, low rating: 2 projects or fewer, low satisfaction and a low evaluation. Overloaded: 6 projects or more, or 270 hours a month or more. Strong performers: 5 to 6 years of tenure with a high evaluation and high satisfaction.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "Which employees get a retention offer."), ("Objective", "The highest saving: replacement cost avoided, less the cost of the offers."),
          ("Method", f'Logistic regression and a random forest in R on {r["dup"]["unique"]:,} employee profiles: 70% to train, 30% to test.')])}
  {notes([f'Risk is not a straight line: employees with too little work and employees with too much work both leave. This is why the main-effects model fails (AUC {base["auc"]:.2f}) and the forest does not (AUC {best["auc"]:.2f}).',
          f'One offer does not fit all three groups. The overloaded group needs less work, not a bonus. Outside the three groups, only {other["rate"]:.0f}% of employees leave.',
          f'The file has {r["dup"]["rows"]:,} rows but only {r["dup"]["unique"]:,} different profiles. The repeats were removed before the split, so that the same profile is not in the training and the test data.',
          "The saving depends on the three assumptions. With a lower success rate of the offer, the cutoff goes up and fewer employees get an offer."])}
</section>"""
    out(slug, html)
    E_[slug] = dict(title="Which employees to approach with a retention offer", industry="general", tasks=["ml"], tools=["r"],
        result=f'Approach the {best["flagged"] / n * 100:.0f}% of employees with a leave risk above {r["cutoff"] * 100:.0f}%. The offers reach {best["recall"]:.0f}% of the leavers and save ${best["saving"] / 1e6:.1f}M for {n:,} employees.',
        method="Logistic regression and a random forest in R, scored by the saving of a retention program",
        scq=["About 1 employee in 6 leaves the company. To replace an employee costs about $25,000.", "A retention offer costs $10,000 and does not always work, so the company cannot make an offer to all employees. It does not know who will leave.", "Which employees must get an offer?"],
        tree_h="The saving depends on who gets an offer; the model and the cutoff are the two levers",
        tree=N("Saving of the retention program", f'${best["saving"] / 1e6:.2f}M on the test employees', "root", c=[
            N("Replacement cost avoided", c=[
                N("Leavers who get an offer", "The lever: the model that ranks employees", "lever", "Does the model find the leavers?", "Yes", f'{best["recall"]:.0f}% of them, with a random forest.'),
                N("Success of an offer", "Fixed: 60% (assumption)", "fixed"), N("Cost to replace an employee", "Fixed: $25,000 (assumption)", "fixed")]),
            N("Cost of the offers", c=[
                N("Offers made", "The lever: the risk cutoff", "lever", "Above which risk does an offer pay?", f'{r["cutoff"] * 100:.0f}%', "$10,000 divided by 60% of $25,000."),
                N("Offers to employees who would stay", "The limit: wasted cost", "limit", "How many offers are wasted?", f'{best["false_alarms"]} of {best["flagged"]}', f'{best["precision"]:.0f}% of the offers go to a leaver.')])]))

def hotel():
    slug = "hotel-cancellation-overbooking"; r = load(slug); ms = {m["model"]: m for m in r["models"]}; lg = ms["Logistic regression"]; fl = ms["Flat rate by hotel"]
    top = max(m["walked"] for m in ms.values())
    order = ["Logistic regression", "Decision tree", "Random forest", "Flat rate by hotel"]
    rows = "".join(bar(f'<b>{k}</b>off by {ms[k]["mae"]:.1f} cancellations a day on average', ms[k]["walked"] / top * 100, f'{ms[k]["walked"]:,.0f}',
                       f'guests with no room, on {ms[k]["days_walked"]:.0f} of {ms[k]["days"]:.0f} days<br>{ms[k]["recovered"]:,.0f} bookings recovered', on=k == "Logistic regression", wide=True, neg=k == "Flat rate by hotel") for k in order)
    L = r["by_lead"]; lt = max(L.values()); lrows = "".join(bar(k, v / lt * 100, f"{v:.0f}%", f'{r["lead_n"][k]:,} bookings', on=i == len(L) - 1) for i, (k, v) in enumerate(L.items()))
    html = kpis([
        ("Bookings recovered by overbooking", f'{lg["recovered"]:,.0f}', f'{lg["recovered"] / lg["cancels"] * 100:.0f}% of the {lg["cancels"]:,.0f} cancellations in the test period'),
        ("Guests with no room", f'{lg["walked"]:.0f}', f'{fl["walked"]:.0f} with one flat cancellation rate for each hotel'),
        ("Error in cancellations for one day", f'{lg["mae"]:.1f}', f'{fl["mae"]:.1f} with the flat rate; about {lg["bookings"] / lg["days"]:.0f} bookings arrive each day'),
    ]) + f"""
<section class="part"><h2>With the risk of each booking, the hotel overbooks about as many rooms and turns away 9 times fewer guests</h2>
  <div class="cp-bars" role="img" aria-label="Guests with no room under each method of overbooking.">{rows}</div>
  <p class="cp-note">For each hotel and arrival day, the hotel overbooks by the expected number of cancellations less one standard deviation. Models were fitted on arrivals in 2015 and 2016 and tested on {r["test_rows"]:,} bookings that arrive in 2017.</p>
</section>
<section class="part"><h2>The time between booking and arrival is the clearest sign of a cancellation</h2>
  <div class="cp-bars" role="img" aria-label="Cancellation rate by lead time.">{lrows}</div>
  <p class="cp-note">Share of bookings that are cancelled, by days between booking and arrival. All {r["rows"]:,} bookings; {r["cancel_rate"]:.0f}% are cancelled in total.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "How many bookings to accept above capacity, for each hotel and arrival day."), ("Objective", "Fill the rooms that cancellations leave empty, with few guests turned away."),
          ("Method", "Logistic regression, a decision tree and a random forest in R, with inputs that the hotel knows when the booking is made.")])}
  {notes([f'The three models rank bookings about equally well (AUC {ms["Decision tree"]["auc"]:.2f} to {ms["Random forest"]["auc"]:.2f}). The logistic regression turns away the fewest guests, so the simple model is the one to use.',
          f'Bookings with no special request are cancelled {r["by_requests"]["0"]:.0f}% of the time, against {r["by_requests"]["1"]:.0f}% with one request. A request is a sign that the guest plans to come.',
          f'Almost all bookings with a non-refundable deposit are recorded as cancelled ({r["by_deposit"]["Non Refund"]:.0f}%). This is a known feature of this public data set and must be checked before the model is used in a hotel.',
          "The reservation status, the assigned room and later booking changes are not model inputs: the hotel does not know them when the booking is made."])}
</section>"""
    out(slug, html)
    E_[slug] = dict(title="How many rooms a hotel can overbook, given the cancellation risk of each booking", industry="travel", tasks=["ml", "pricing"], tools=["r"],
        result=f'A model of cancellation risk recovers {lg["recovered"]:,.0f} cancelled bookings in the test period and turns away {lg["walked"]:.0f} guests. A flat-rate rule turns away {fl["walked"]:.0f}.',
        method="Cancellation models in R on 119,390 public hotel bookings, tested on a later year",
        scq=["Two hotels took about 119,000 bookings in two years. 37% of the bookings were cancelled.", "A cancelled booking leaves an empty room. The hotels can overbook, but with one average cancellation rate they turn away guests on the days when few bookings cancel.", "How many bookings can a hotel accept above capacity on each day?"],
        tree_h="Overbooking trades empty rooms against guests with no room; a better forecast improves the two at the same time",
        tree=N("Cost of cancellations", "", "root", c=[
            N("Rooms left empty", c=[
                N("Bookings accepted above capacity", "The lever: expected cancellations less a safety margin", "lever", "How many cancellations does overbooking recover?", f'{lg["recovered"] / lg["cancels"] * 100:.0f}%', f'{lg["recovered"]:,.0f} of {lg["cancels"]:,.0f} in the test period.'),
                N("Cancellations", "Fixed: 37% of bookings", "fixed")]),
            N("Guests with no room", c=[
                N("Forecast of cancellations for one day", "The lever: the risk of each booking", "lever", "Is a model better than one flat rate?", "Yes", f'Error of {lg["mae"]:.1f} cancellations a day against {fl["mae"]:.1f}.'),
                N("Guests turned away", "The limit", "limit", "How many guests have no room?", f'{lg["walked"]:.0f}', f'On {lg["days_walked"]:.0f} of {lg["days"]:.0f} hotel-days; {fl["walked"]:.0f} with the flat rate.')])]))

def hits():
    slug = "hit-song-prediction"; r = load(slug); ms = r["models"]; best = ms[-1]; snd = ms[0]; top = max(m["precision"] for m in ms)
    rows = "".join(bar(f'<b>{m["model"]}</b>AUC {m["auc"]:.2f}', m["precision"] / top * 100, f'{m["precision"]:.0f}%', f'{m["hits"]:,} hits in {m["picks"]:,} picks', on=m is best, wide=True) for m in ms)
    rows += bar("<b>Picks at random</b>no model", r["test_hit_rate"] / top * 100, f'{r["test_hit_rate"]:.0f}%', "the share of hits in all new tracks", wide=True)
    A = r["by_artist"]; at = max(a["hit_rate"] for a in A); arows = "".join(bar(a["group"], a["hit_rate"] / at * 100, f'{a["hit_rate"]:.0f}%', f'{a["tracks"]:,} tracks', on=a["group"].startswith("More")) for a in A)
    imp = r["importance"]; snd_imp = 100 - imp["genre_hit_rate"] - imp["artist_hit_share"] - imp["artist_tracks"] - imp["new_artist"]
    html = kpis([
        ("Hits among the top 10% of picks", f'{best["precision"]:.0f}%', f'{r["test_hit_rate"]:.0f}% for all new tracks: {best["lift"]:.1f} times better than chance'),
        ("With the sound of the track only", f'{snd["precision"]:.0f}%', "audio measures such as energy, tempo and loudness"),
        ("Hits that the picks contain", f'{best["found"]:.0f}%', f'{best["hits"]:,} of the hits, from 10% of the tracks'),
    ]) + f"""
<section class="part"><h2>The sound says little; genre and the record of the artist give most of the gain</h2>
  <div class="cp-bars" role="img" aria-label="Share of hits among the top 10% of picks, by model.">{rows}</div>
  <p class="cp-note">A hit is a track in the top quarter of popularity among the tracks of the same release year. Models were fitted on releases from 2000 to 2021 and tested on {r["test_rows"]:,} tracks released in 2022 and 2023.</p>
</section>
<section class="part"><h2>An artist with a record of hits is the safest pick, and a new artist is a better pick than an artist with no hit</h2>
  <div class="cp-bars" role="img" aria-label="Share of hits by the record of the artist.">{arows}</div>
  <p class="cp-note">Record of the artist in the years before the track: share of earlier tracks that were hits. Test tracks, 2022 and 2023.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "Which new tracks get a place in the promotion plan."), ("Objective", "The highest share of hits among the tracks picked."),
          ("Method", f'Logistic regressions and a random forest in R on {r["rows"]:,} tracks by {r["artists"]:,} artists (a 25% sample of a public file).')])}
  {notes([f'In the random forest, genre and the record of the artist carry {100 - snd_imp:.0f}% of the importance. The eleven audio measures share the other {snd_imp:.0f}%.',
          "The popularity score favors recent tracks. With one cutoff for all years, the model learns which tracks are new. The hit label is set inside each release year to remove this.",
          "The record of the artist uses earlier years only, so the model knows nothing that a label does not know at release.",
          "Genre is strong in part because of how the public file was collected, by genre lists. A label must test the model on its own catalog."])}
</section>"""
    out(slug, html)
    E_[slug] = dict(title="Which new tracks a music label must promote first", industry="consumer", tasks=["ml"], tools=["r"],
        result=f'A model picks a top 10% of new tracks in which {best["precision"]:.0f}% are hits, against {r["test_hit_rate"]:.0f}% for all tracks. Genre and the record of the artist decide; the sound adds little.',
        method="Hit prediction models in R on 289,941 public Spotify tracks, tested on later release years",
        scq=["A music label releases many tracks each year and has promotion money for a small part of them.", "About 1 track in 4 becomes a hit. The label must choose which tracks to promote at release, before there are streaming numbers.", "Can a model find the hits at release, and what does it use?"],
        tree_h="The return on promotion depends on the share of hits among the picks; three kinds of information can raise it",
        tree=N("Hits among the tracks promoted", f'{best["precision"]:.0f}% in the answer', "root", c=[
            N("Tracks picked", c=[N("Promotion budget", "The limit: the top 10% of new tracks", "limit")]),
            N("Information at release", c=[
                N("Sound of the track", "Eleven audio measures", "", "Does the sound predict a hit?", "A little", f'{snd["precision"]:.0f}% hits among the picks, against {r["test_hit_rate"]:.0f}% at random.'),
                N("Genre", "", "", "Does genre add to the sound?", "Yes", f'{ms[1]["precision"]:.0f}% hits among the picks.'),
                N("Record of the artist", "The lever: earlier tracks and earlier hits", "lever", "Does the record add more?", "Yes", f'{best["precision"]:.0f}% with all inputs. Artists with more than 50% earlier hits: {A[-1]["hit_rate"]:.0f}% of new tracks are hits.')])]))

if __name__ == "__main__":
    retention(); hotel(); hits()
    d = json.load(open("data/projects.json", encoding="utf-8"))
    if not any(i["id"] == "general" for i in d["industries"]): d["industries"].append({"id": "general", "name": "Cross-industry"})
    d["projects"] = [p for p in d["projects"] if p.get("slug") not in E_]
    i = [k for k, p in enumerate(d["projects"]) if p.get("slug") == "telemarketing-call-list"][0] + 1
    d["projects"][i:i] = [dict(slug=s, type="course", org=M, files=[["r", "R script", "Models and the business result", "analysis.R"]], **v) for s, v in E_.items()]
    json.dump(d, open("data/projects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", list(E_))
