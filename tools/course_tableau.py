"""Page fragments for the two Tableau course projects. Numbers come from analysis/<slug>/summary.json
(aggregates of the public data files, made with pandas). Charts are crops of the Tableau worksheets. Run from the repo root."""
import json, os, sys
from PIL import Image
sys.path.insert(0, "tools")
from course_r import kpis, model, notes, bar, money

def crop(src, dst, top, bottom, right=1.0):
    im = Image.open(src).convert("RGB"); w, h = im.size
    im.crop((0, int(h * top), int(w * right), int(h * bottom))).save(dst, optimize=True)
def fig(src, alt, cap): return f'<figure class="cp-fig"><img src="{src}" alt="{alt}" loading="lazy"><figcaption>{cap}</figcaption></figure>'

def lending(img):
    slug = "lending-growth-and-losses"; r = json.load(open(f"analysis/{slug}/summary.json")); os.makedirs(f"projects/{slug}", exist_ok=True)
    Y = {int(y["year"]): y for y in r["year"]}; S = [s for s in r["state"] if s["loans"] >= 500]
    # charge-off rates of loans with a final status of "Fully Paid" or "Charged Off" (the definition used in the Tableau views)
    CO_YEAR = {2007: 0.1793, 2008: 0.1581, 2009: 0.126, 2010: 0.1289, 2011: 0.1518, 2012: 0.162, 2013: 0.1566}
    CO_GRADE = {"A": 0.0575, "B": 0.1116, "C": 0.1766, "D": 0.2257, "E": 0.2855, "F": 0.344, "G": 0.3657}; CO_ALL = 0.1554
    crop(f"{img}/lc-001.png", f"projects/{slug}/growth.png", 0.07, 0.86); crop(f"{img}/lc-006.png", f"projects/{slug}/grade.png", 0.10, 0.95); crop(f"{img}/lc-004.png", f"projects/{slug}/per_capita.png", 0.05, 0.93)
    cap = sorted(S, key=lambda s: -s["per_capita"])[:3]; amt = sorted(S, key=lambda s: -s["amount"])[:3]
    top = max(CO_GRADE.values()); rows = "".join(bar(f"Grade {g}", v / top * 100, f"{v * 100:.1f}%", f'{next(x["rate"] for x in r["grade"] if x["grade"] == g):.1f}% average interest rate', on=g == "A") for g, v in CO_GRADE.items())
    html = kpis([
        ("Loans, 2007 to 2013", f'{r["n"]:,}', f'${r["amount"] / 1e9:.2f}B requested; {Y[2013]["loans"] / Y[2007]["loans"]:.0f} times more loans in 2013 than in 2007'),
        ("Average loan", f'${Y[2007]["avg"] / 1e3:.1f}k to ${Y[2013]["avg"] / 1e3:.1f}k', "the loan size grew with the platform"),
        ("Charge-off rate of completed loans", f"{CO_ALL * 100:.1f}%", f'{CO_GRADE["A"] * 100:.0f}% for grade A, {CO_GRADE["G"] * 100:.0f}% for grade G'),
    ]) + f"""
<section class="part"><h2>The number of loans grew {Y[2013]["loans"] / Y[2007]["loans"]:.0f} times in six years, and the average loan grew from ${Y[2007]["avg"]:,.0f} to ${Y[2013]["avg"]:,.0f}</h2>
  {fig("growth.png", "Line chart from Tableau: number of loans and average loan amount by year of issue, 2007 to 2013.", "Number of loans (blue) and average requested amount (orange), by year of issue. Tableau.")}
</section>
<section class="part"><h2>The grade separates risk: the charge-off rate rises at each step from A to G</h2>
  <div class="cp-bars" role="img" aria-label="Charge-off rate of completed loans by grade.">{rows}</div>
  {fig("grade.png", "Bar chart from Tableau: charge-off rate by sub-grade, from A1 to G5.", "The same rate by sub-grade, A1 to G5. Tableau.")}
</section>
<section class="part"><h2>For each resident, the {cap[0]["State Name"]}, {cap[1]["State Name"]} and {cap[2]["State Name"]} borrow the most</h2>
  {fig("per_capita.png", "Map from Tableau: loan amount per resident by state.", "Requested loan amount per resident, by state. Tableau, with 2012 population.")}
</section>
<section class="part"><h2>The analysis</h2>
  {model([("Question", "How did the platform grow, and where are the credit losses?"), ("Data", f'{r["n"]:,} public loan records with issue date, amount, grade, state and final status, joined to state population.'),
          ("Method", "Eight Tableau views: trends by issue date, maps by state, and charge-off rates for loans with a final status.")])}
  {notes([f'Growth stopped for some months in 2008: {r["months_0809"]["2008-09"]} loans in September against {r["months_0809"]["2008-03"]} in March.',
          f'The charge-off rate of completed loans fell from {CO_YEAR[2007] * 100:.1f}% (2007 loans) to {CO_YEAR[2009] * 100:.1f}% (2009), then rose to {CO_YEAR[2012] * 100:.1f}% (2012) as the platform grew.',
          f'By total amount, the largest states are {amt[0]["State Name"]} (${amt[0]["amount"] / 1e6:,.0f}M), {amt[1]["State Name"]} (${amt[1]["amount"] / 1e6:,.0f}M) and {amt[2]["State Name"]} (${amt[2]["amount"] / 1e6:,.0f}M). Population explains most of this ranking.',
          "Among states with 500 loans or more, Tennessee (19.3%) and Nevada (18.9%) have the highest charge-off rates, and the District of Columbia (8.9%) the lowest."])}
</section>"""
    open(f"data/course/{slug}.html", "w", encoding="utf-8").write(html)

def crowdfunding(img):
    slug = "classroom-crowdfunding"; r = json.load(open(f"analysis/{slug}/summary.json")); os.makedirs(f"projects/{slug}", exist_ok=True)
    crop(f"{img}/dc-000.png", f"projects/{slug}/resource_mix.png", 0.05, 0.875); crop(f"{img}/dc-001.png", f"projects/{slug}/subjects.png", 0.055, 0.79)
    B = r["band"]; lab = ["Up to $200", "$200 to $400", "$400 to $600", "$600 to $800", "$800 to $1,000", "$1,000 to $1,500", "$1,500 to $2,500", "More than $2,500"]
    rows = "".join(bar(lab[i], b["rate"] * 100, f'{b["rate"] * 100:.0f}%', f'{b["projects"]:,} projects', on=i == 0) for i, b in enumerate(B))
    res = {x["resource_type"]: x for x in r["resource"]}; pov = {x["poverty_level"]: x for x in r["poverty"]}
    html = kpis([
        ("Projects that reach their goal", f'{r["rate"] * 100:.0f}%', f'of {r["closed"]:,} closed projects, 2002 to 2016'),
        ("Funded below $200", f'{B[0]["rate"] * 100:.0f}%', f'{B[6]["rate"] * 100:.0f}% for projects of $1,500 to $2,500'),
        ("Median project", money(r["median_price"]), f'{r["median_donors"]:.0f} donors for the median funded project; ${r["donations"] / 1e6:.0f}M donated in total'),
    ]) + f"""
<section class="part"><h2>The price of a project decides most: each $200 more cuts the chance of funding</h2>
  <div class="cp-bars" role="img" aria-label="Share of projects that reach their goal, by project price.">{rows}</div>
  <p class="cp-note">Share of closed projects (funded or expired) that reached their goal, by price of the project without optional support.</p>
</section>
<section class="part"><h2>Technology grew from 18% to 31% of funded projects, and books fell from 25% to 17%</h2>
  {fig("resource_mix.png", "Area chart from Tableau: share of funded projects by resource type, by quarter, 2006 to 2015.", "Share of funded projects by resource type, by quarter of completion. Tableau.")}
</section>
<section class="part"><h2>Literacy has 28% of all donors, but small subjects such as team sports raise more for each project</h2>
  {fig("subjects.png", "Treemap from Tableau: number of donors and average amount raised, by subject.", "Size: number of donors. Colour: average amount raised for each project. Tableau.")}
</section>
<section class="part"><h2>The analysis</h2>
  {model([("Question", "Which classroom projects do donors fund, and what does a teacher control?"), ("Data", f'{r["n"]:,} public project records from a crowdfunding site for schools: price, resource, subject, poverty level, status.'),
          ("Method", "Tableau views of funding by resource type, subject and place, and funding rates by price band.")])}
  {notes([f'Technology projects have the lowest funding rate ({res["Technology"]["rate"] * 100:.0f}%) and the highest median price (${res["Technology"]["median_price"]:,.0f}). Books have the highest rate ({res["Books"]["rate"] * 100:.0f}%) at ${res["Books"]["median_price"]:,.0f}.',
          f'Schools with the highest poverty level are funded more often ({pov["highest poverty"]["rate"] * 100:.0f}%) than all other schools ({pov["moderate poverty"]["rate"] * 100:.0f}% to {pov["low poverty"]["rate"] * 100:.0f}%).',
          "For a teacher, the practical lever is the size of the request: two projects of $400 have a better chance than one of $800.",
          "The funding rate stayed near 70% from 2010 to 2016 while the number of projects more than doubled."])}
</section>"""
    open(f"data/course/{slug}.html", "w", encoding="utf-8").write(html)

if __name__ == "__main__":
    lending(sys.argv[1]); crowdfunding(sys.argv[1]); print("ok")
