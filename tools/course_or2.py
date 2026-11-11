"""Three more course projects: sealed bid (decision tree), room protection (Monte Carlo), production plan (integer program).
Writes page fragments, Excel models and Python scripts. Run from the repo root."""
import os, sys, math, inspect
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds, minimize_scalar
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter as L
sys.path.insert(0, "tools")
from course_r import kpis, model, notes, bar, money

F = lambda size=10, **k: Font(name="Arial", size=size, **k)
HEAD = PatternFill("solid", fgColor="051C2C"); PICK = PatternFill("solid", fgColor="FFFF00")
def head(ws, r, c, v):
    x = ws.cell(r, c, v); x.font = F(bold=True, color="FFFFFF"); x.fill = HEAD; x.alignment = Alignment(horizontal="center", wrap_text=True)
def inp(ws, r, c, v, fmt=None):
    x = ws.cell(r, c, v); x.font = F(color="0000FF")
    if fmt: x.number_format = fmt
    return x
def lab(ws, r, c, v, bold=False, fmt=None):
    x = ws.cell(r, c, v); x.font = F(bold=bold)
    if fmt: x.number_format = fmt
    return x
def save(slug, html, files):
    os.makedirs(f"projects/{slug}", exist_ok=True)
    open(f"data/course/{slug}.html", "w", encoding="utf-8").write(html)
    for name, text in files.items(): open(f"projects/{slug}/{name}", "w", encoding="utf-8").write(text)

# =================================================================== 1. sealed bid
NPV, CAPITAL, P_OK, FORFEIT = 15.0, 8.0, 0.30, 0.10
def p_win(b): return 1 / (1 + math.exp(5 - 0.723 * b))
def if_win(b): return P_OK * (NPV - CAPITAL - b) + (1 - P_OK) * (-FORFEIT * b)
def ev(b): return p_win(b) * if_win(b)

def bid():
    slug = "sealed-bid-decision"
    opt = minimize_scalar(lambda b: -ev(b), bounds=(0, 10), method="bounded", options={"xatol": 1e-9}); b = opt.x
    even = (P_OK * (NPV - CAPITAL)) / (P_OK + (1 - P_OK) * FORFEIT)      # highest bid with a positive expected value
    need = FORFEIT * 5 / (NPV - CAPITAL - 5 + FORFEIT * 5)                # approval probability that makes a $5M bid break even
    assert abs(b - 4.11) < 0.01 and abs(ev(b) - 0.0674) < 0.0005 and abs(ev(5) - 0.05) < 1e-3 and abs(need - 0.2) < 1e-9
    top = ev(b); rows = ""
    for x in [3.0, 3.5, 4.0, round(b, 2), 4.5, 5.0, 5.5, 6.0]:
        v = ev(x)
        rows += bar(f"${x:.2f}M" if x == round(b, 2) else f"${x:.1f}M", max(v, 0) / top * 100, f"${v * 1000:,.0f}k", f"wins {p_win(x) * 100:.0f}% of the time", on=x == round(b, 2), neg=v < 0)
    pw = p_win(b)
    html = kpis([
        ("Bid with the highest expected value", f"${b:.2f}M", f"expected value ${ev(b) * 1000:,.0f}k; ${ev(5) * 1000:,.0f}k at the planned $5M bid"),
        ("Chance to win at that bid", f"{pw * 100:.0f}%", f"{p_win(5) * 100:.0f}% at $5M: a higher bid wins more often but leaves less"),
        ("Highest bid that is not a loss on average", f"${even:.2f}M", "above this, the expected value is negative"),
    ]) + f"""
<section class="part"><h2>The expected value has its maximum at $4.11M and goes below zero above $5.68M</h2>
  <div class="cp-bars" role="img" aria-label="Expected value of the project for each bid.">{rows}</div>
  <p class="cp-note">Chance to win = 1 / (1 + e^(5 − 0.723 × bid)), bid in $ million. If the bid wins, the plan needs an approval ({P_OK * 100:.0f}% chance). With approval the project earns ${NPV:.0f}M less ${CAPITAL:.0f}M of capital and the bid. Without it the bidder loses {FORFEIT * 100:.0f}% of the bid.</p>
</section>
<section class="part"><h2>Most of the time nothing happens; the gain comes from a 3% outcome</h2>
  <div class="table-scroll"><table class="cp-table">
    <caption>Outcomes of a ${b:.2f}M bid</caption>
    <thead><tr><th scope="col">Outcome</th><th scope="col" class="n">Probability</th><th scope="col" class="n">Result</th></tr></thead>
    <tbody><tr><td>The bid loses</td><td class="n">{(1 - pw) * 100:.1f}%</td><td class="n">$0</td></tr>
    <tr><td>The bid wins, the plan is not approved</td><td class="n">{pw * (1 - P_OK) * 100:.1f}%</td><td class="n neg">−${FORFEIT * b:.2f}M</td></tr>
    <tr><td>The bid wins, the plan is approved</td><td class="n">{pw * P_OK * 100:.1f}%</td><td class="n strong">+${NPV - CAPITAL - b:.2f}M</td></tr></tbody>
  </table></div>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "The amount of one sealed bid for a property."), ("Objective", "The highest expected value of the project."),
          ("Uncertainty", "Two events in sequence: the bid wins or loses, then the plan is approved or not. The chance to win goes up with the bid.")])}
  {notes([f"With a fixed {p_win(5) * 100:.0f}% chance to win, a $5M bid is worth ${ev(5) * 1000:,.0f}k. When the chance to win depends on the bid, a lower bid of ${b:.2f}M is worth {(ev(b) / ev(5) - 1) * 100:.0f}% more.",
          f"A $5M bid breaks even at an approval chance of {need * 100:.0f}%. The estimate is {P_OK * 100:.0f}%, so the margin for error is 10 points.",
          f"The expected value is small against the stakes: ${ev(b) * 1000:,.0f}k against a possible loss of ${FORFEIT * b * 1000:,.0f}k. A bidder who cannot take that loss must not bid.",
          "The win curve is an assumption. The first thing to test is how the answer moves when the curve moves."])}
</section>"""
    wb = Workbook(); ws = wb.active; ws.title = "Model"
    lab(ws, 1, 1, "Sealed bid: decision tree with a bid-dependent chance to win", True).font = F(14, bold=True)
    lab(ws, 2, 1, "Blue cells are inputs. The yellow cell is the decision. Amounts are in $ million.")
    for r, (t, v, f) in enumerate([("Value of the project if approved (NPV)", NPV, "0.00"), ("Capital needed", CAPITAL, "0.00"), ("Chance of approval", P_OK, "0%"), ("Share of the bid lost if not approved", FORFEIT, "0%"),
                                   ("Win curve: constant", 5, "0.000"), ("Win curve: slope per $ million", 0.723, "0.000")], 4):
        lab(ws, r, 1, t); inp(ws, r, 2, v, f)
    lab(ws, 11, 1, "Bid", True); c = ws.cell(11, 2, 5); c.fill = PICK; c.font = F(bold=True); c.number_format = "0.00"
    lab(ws, 12, 1, "Chance to win"); lab(ws, 12, 2, "=1/(1+EXP($B$8-$B$9*B11))", fmt="0.0%")
    lab(ws, 13, 1, "Result if the bid wins and the plan is approved"); lab(ws, 13, 2, "=$B$4-$B$5-B11", fmt="0.00")
    lab(ws, 14, 1, "Result if the bid wins and the plan is not approved"); lab(ws, 14, 2, "=-$B$7*B11", fmt="0.00")
    lab(ws, 15, 1, "Expected result if the bid wins"); lab(ws, 15, 2, "=$B$6*B13+(1-$B$6)*B14", fmt="0.000")
    lab(ws, 16, 1, "Expected value of the bid", True); lab(ws, 16, 2, "=B12*B15", True, "0.0000")
    lab(ws, 18, 1, "Best bid in the table to the right"); lab(ws, 18, 2, "=INDEX(D5:D85,MATCH(MAX(G5:G85),G5:G85,0))", True, "0.00")
    lab(ws, 19, 1, "Expected value at the best bid"); lab(ws, 19, 2, "=MAX(G5:G85)", True, "0.0000")
    lab(ws, 20, 1, "Highest bid with a positive expected value"); lab(ws, 20, 2, "=$B$6*($B$4-$B$5)/($B$6+(1-$B$6)*$B$7)", fmt="0.00")
    for k, t in enumerate(["Bid", "Chance to win", "Expected result if the bid wins", "Expected value"]): head(ws, 4, 4 + k, t)
    for i in range(81):
        r = 5 + i; inp(ws, r, 4, round(i * 0.1, 1), "0.0")
        lab(ws, r, 5, f"=1/(1+EXP($B$8-$B$9*D{r}))", fmt="0.0%"); lab(ws, r, 6, f"=$B$6*($B$4-$B$5-D{r})+(1-$B$6)*(-$B$7*D{r})", fmt="0.000"); lab(ws, r, 7, f"=E{r}*F{r}", fmt="0.0000")
    ws.column_dimensions["A"].width = 52; ws.column_dimensions["B"].width = 12
    for c in "DEFG": ws.column_dimensions[c].width = 18
    wb.save(f"projects/{slug}/bid_model.xlsx") if os.path.isdir(f"projects/{slug}") else (os.makedirs(f"projects/{slug}"), wb.save(f"projects/{slug}/bid_model.xlsx"))
    save(slug, html, {})

# =================================================================== 2. room protection
CABINS, GUESTS, LOW = 10, 100, 100
def simulate(protect, high, nights=20000, seed=7):
    """Mean revenue per night. Guests arrive one at a time. The low rate applies until only `protect` cabins are left."""
    rng = np.random.default_rng(seed)
    business = rng.random((nights, GUESTS)) < 0.05
    wtp = np.where(business, rng.normal(300, 45, (nights, GUESTS)), rng.normal(100, 25, (nights, GUESTS)))
    left = np.full(nights, CABINS); revenue = np.zeros(nights)
    for g in range(GUESTS):
        rate = np.where(left <= protect, high, LOW)
        book = (wtp[:, g] >= rate) & (left > 0)
        revenue += rate * book; left = left - book
    return revenue.mean(), revenue.std(), left.mean()

def rooms():
    slug = "room-protection-pricing"
    highs = list(range(160, 361, 20)); grid = {(p, h): simulate(p, h)[0] for p in range(0, 11) for h in highs}
    (bp, bh), best = max(grid.items(), key=lambda kv: kv[1])
    fine = {(p, h): simulate(p, h, 60000, 11)[0] for p in (bp - 1, bp, bp + 1) for h in range(bh - 20, bh + 21, 10)}
    (bp, bh), best = max(fine.items(), key=lambda kv: kv[1])
    m, s, empty = simulate(bp, bh, 60000, 11); base = simulate(0, bh)[0]; now = simulate(3, 220, 60000, 11)[0]
    lo, hi = min(grid.values()), max(grid.values())
    th = "".join(f'<th scope="col" class="n">${h}</th>' for h in highs); body = ""
    for p in range(0, 11):
        tds = ""
        for h in highs:
            v = grid[(p, h)]; a = (v - lo) / (hi - lo)
            tds += f'<td class="n{" best" if (p, h) == (bp, bh) else ""}" style="background:rgba(34,81,255,{a * 0.55:.2f})">{v:,.0f}</td>'
        body += f'<tr><th scope="row">{p}</th>{tds}</tr>'
    html = kpis([
        ("Best policy", f"Hold {bp}, at ${bh}", f"the last {bp} of 10 cabins sell only at the full rate"),
        ("Revenue per night", money(m), f"+{(m / base - 1) * 100:.0f}% against one rate of ${LOW} for all cabins (${base:,.0f})"),
        ("Cabins that stay empty", f"{empty:.1f} of 10", "on an average night: the cost of the wait for guests who pay more"),
    ]) + f"""
<section class="part"><h2>Revenue is highest when 4 cabins are held for a full rate near $260</h2>
  <div class="table-scroll"><table class="cp-grid heatgrid">
    <caption>Average revenue per night ($), by number of cabins held back (rows) and full rate (columns). 20,000 simulated nights for each cell.</caption>
    <thead><tr><th scope="col">Held</th>{th}</tr></thead><tbody>{body}</tbody>
  </table></div>
  <p class="cp-note">Each night 100 guests ask for a cabin, one at a time. 95% are leisure guests who pay $100 on average (standard deviation $25). 5% are business guests who pay $300 on average (standard deviation $45). A guest books when the rate is at or below what the guest will pay.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "How many of the 10 cabins to hold back, and the full rate for those cabins."), ("Objective", "The highest average revenue per night."),
          ("Method", "Monte Carlo simulation of the guests of one night, for each pair of protection level and full rate.")])}
  {notes([f"A policy of 3 cabins at $220 earns ${now:,.0f}. The best policy earns {(m / now - 1) * 100:.0f}% more.",
          f"The top of the table is flat: 4 or 5 cabins at $240 or $260 are all within {(1 - min(grid[(p, h)] for p in (4, 5) for h in (240, 260)) / hi) * 100:.0f}% of the best policy. An exact value is not necessary.",
          f"A full rate above $300 loses money quickly, because few business guests will pay it and the held cabins stay empty.",
          "The result depends on the 5% share of business guests. The lodge must measure that share before it changes the policy."])}
</section>"""
    wb = Workbook(); ws = wb.active; ws.title = "One night"
    lab(ws, 1, 1, "Room protection: simulation of one night", True).font = F(14, bold=True)
    lab(ws, 2, 1, "Blue cells are inputs. Yellow cells are the decision. Press F9 for a new night. The Results sheet has the averages over 20,000 nights.")
    for r, (t, v) in enumerate([("Cabins", CABINS), ("Low rate ($)", LOW), ("Share of business guests", 0.05), ("Leisure: mean of the amount a guest will pay ($)", 100), ("Leisure: standard deviation ($)", 25),
                                ("Business: mean ($)", 300), ("Business: standard deviation ($)", 45)], 4):
        lab(ws, r, 1, t); inp(ws, r, 2, v)
    ws["B6"].number_format = "0%"
    lab(ws, 12, 1, "Cabins held back", True); lab(ws, 13, 1, "Full rate ($)", True)
    for r, v in ((12, bp), (13, bh)):
        c = ws.cell(r, 2, v); c.fill = PICK; c.font = F(bold=True)
    lab(ws, 15, 1, "Revenue of this night ($)", True); lab(ws, 15, 2, "=SUM(J5:J104)", True, "#,##0")
    lab(ws, 16, 1, "Cabins sold"); lab(ws, 16, 2, "=SUM(I5:I104)")
    for k, t in enumerate(["Guest", "Business? (1 = yes)", "Will pay ($)", "Cabins left", "Rate ($)", "Books? (1 = yes)", "Revenue ($)"]): head(ws, 4, 4 + k, t)
    for i in range(GUESTS):
        r = 5 + i; lab(ws, r, 4, i + 1)
        lab(ws, r, 5, "=IF(RAND()<$B$6,1,0)"); lab(ws, r, 6, f"=NORMINV(RAND(),IF(E{r}=1,$B$9,$B$7),IF(E{r}=1,$B$10,$B$8))", fmt="0")
        lab(ws, r, 7, "=$B$4" if i == 0 else f"=G{r - 1}-I{r - 1}"); lab(ws, r, 8, f"=IF(G{r}<=$B$12,$B$13,$B$5)")
        lab(ws, r, 9, f"=IF(AND(H{r}<=F{r},G{r}>0),1,0)"); lab(ws, r, 10, f"=H{r}*I{r}")
    ws.column_dimensions["A"].width = 50; ws.column_dimensions["B"].width = 12
    for c in "DEFGHIJ": ws.column_dimensions[c].width = 14
    s2 = wb.create_sheet("Results")
    lab(s2, 1, 1, "Average revenue per night ($). Source: simulate.py, 20,000 nights for each cell, random seed 7.", True)
    head(s2, 3, 1, "Cabins held \\ Full rate ($)")
    for j, h in enumerate(highs): head(s2, 3, 2 + j, h)
    for p in range(0, 11):
        lab(s2, 4 + p, 1, p, True)
        for j, h in enumerate(highs): lab(s2, 4 + p, 2 + j, round(grid[(p, h)], 1), fmt="#,##0")
    lab(s2, 16, 1, "Highest value in the table"); lab(s2, 16, 2, f"=MAX(B4:{L(1 + len(highs))}14)", True, "#,##0")
    s2.column_dimensions["A"].width = 30
    os.makedirs(f"projects/{slug}", exist_ok=True); wb.save(f"projects/{slug}/room_protection_model.xlsx")
    code = ('"""Room protection: Monte Carlo simulation of one night at a 10-cabin lodge."""\nimport numpy as np\n\nCABINS, GUESTS, LOW = 10, 100, 100\n\n\n'
            + inspect.getsource(simulate) + '\n\nif __name__ == "__main__":\n    for protect in range(0, 11):\n        print(protect, [round(simulate(protect, high)[0]) for high in range(160, 361, 20)])\n')
    save(slug, html, {"simulate.py": code})
    return (bp, bh, m, base, now, empty)

# =================================================================== 3. production plan
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

def production():
    slug = "seasonal-production-plan"
    res = {m: plan(m) for m in ("mixed", "level", "chase")}
    cost, x, parts = res["mixed"]; assert abs(cost - 6221280) <= 2000, cost
    names = {"mixed": ("Mixed plan (lowest cost)", "Hire before the peak, add overtime at the peak, then reduce"), "level": ("Level workforce", "One workforce size all year, no overtime, inventory takes the peaks"),
             "chase": ("Production follows demand", "No planned inventory; hires, layoffs and overtime take the peaks")}
    top = max(v[0] for v in res.values()); rows = ""
    for m in ("mixed", "level", "chase"):
        c = res[m][0]; p = res[m][2]
        side = "lowest cost" if m == "mixed" else f"+{money(c - cost)} (+{(c / cost - 1) * 100:.0f}%)"
        rows += bar(f"<b>{names[m][0]}</b>{names[m][1]}", c / top * 100, f"${c / 1e6:.2f}M", side, on=m == "mixed", wide=True)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    th = "".join(f'<th scope="col" class="n">{m}</th>' for m in months)
    def tr(label, vals, cls=""): return f'<tr class="{cls}"><th scope="row">{label}</th>' + "".join(f'<td class="n ok">{v:,}</td>' if v else '<td class="n">0</td>' for v in vals) + "</tr>"
    prod = [PER * (x[3][t] + x[2][t]) for t in range(12)]
    peak_w = x[3].max(); ot_months = [months[t] for t in range(12) if x[2][t]]
    html = kpis([
        ("Lowest cost for the year", f"${cost / 1e6:.2f}M", f"{(1 - cost / res['level'][0]) * 100:.0f}% below a level workforce, {(1 - cost / res['chase'][0]) * 100:.0f}% below production that follows demand"),
        ("Workforce", f"{W0} to {peak_w}", f"hire before the peak, then reduce in steps to {x[3][-1]}"),
        ("Overtime", f"{len(ot_months)} months", f"{' and '.join(ot_months)} only; inventory takes the rest of the peak"),
    ]) + f"""
<section class="part"><h2>The mixed plan costs {(1 - cost / res['level'][0]) * 100:.0f}% less than a level workforce and {(1 - cost / res['chase'][0]) * 100:.0f}% less than production that follows demand</h2>
  <div class="cp-bars" role="img" aria-label="Cost for the year of three production strategies.">{rows}</div>
</section>
<section class="part"><h2>Build inventory before the summer, then use overtime for the last part of the peak</h2>
  <div class="table-scroll"><table class="cp-grid plan">
    <caption>The lowest-cost plan, by month (units and workers)</caption>
    <thead><tr><th scope="col"></th>{th}</tr></thead>
    <tbody>{tr("Demand", DEMAND)}{tr("Production", prod)}{tr("Inventory at month end", list(x[4]))}{tr("Workers", list(x[3]), "cost")}{tr("Hires", list(x[0]), "cost")}{tr("Layoffs", list(x[1]), "cost")}{tr("Workers on overtime", list(x[2]), "cost")}</tbody>
  </table></div>
  <p class="cp-note">One worker makes {PER} units a month for ${SALARY:,}. A hire costs ${HIRE:,}, a layoff ${FIRE:,}, a worker-month of overtime ${OT:,}, and one unit in inventory ${HOLD} a month. The plant makes {CAP:,} units a month at most.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "For each of 12 months: hires, layoffs, workers on overtime. 36 whole-number variables."), ("Objective", "The lowest total of salaries, hire and layoff costs, overtime and inventory cost."),
          ("Constraints", "Demand is met each month from production and inventory. Production is inside plant capacity. Each worker does one overtime shift at most.")])}
  {notes([f"Salaries are 85% to 90% of the cost in each strategy. The strategies differ in how they pay for the peak: inventory (${res['level'][2]['Inventory'] / 1e3:,.0f}k in the level plan) or overtime (${res['chase'][2]['Overtime'] / 1e3:,.0f}k when production follows demand).",
          f"The mixed plan pays ${parts['Inventory'] / 1e3:,.0f}k for inventory and ${parts['Overtime'] / 1e3:,.0f}k for overtime, plus ${(parts['Hires'] + parts['Layoffs']) / 1e3:,.0f}k to change the workforce.",
          f"The whole-number plan costs only ${cost - round(plan('mixed', False)[0]):,} more than the plan with fractions of a worker, so the rounding has no practical effect.",
          "The plan uses one demand forecast. A plan for use must be tested against a high and a low forecast."])}
</section>"""
    # workbook
    wb = Workbook(); ws = wb.active; ws.title = "Plan"
    lab(ws, 1, 1, "Seasonal production plan: workforce, overtime and inventory", True).font = F(14, bold=True)
    lab(ws, 2, 1, "Blue cells are inputs. Yellow cells are the decision (lowest-cost plan from Solver). All other cells are formulas.")
    P = [("Holding cost per unit per month ($)", HOLD), ("Salary per worker per month ($)", SALARY), ("Cost of one hire ($)", HIRE), ("Cost of one layoff ($)", FIRE), ("Overtime per worker per month ($)", OT),
         ("Plant capacity (units per month)", CAP), ("Units per worker per month", PER), ("Workers at the start", W0), ("Inventory at the start (units)", I0)]
    for r, (t, v) in enumerate(P, 4): lab(ws, r, 1, t); inp(ws, r, 2, v)
    head(ws, 14, 1, "Month")
    for t in range(12): head(ws, 14, 2 + t, months[t])
    head(ws, 14, 14, "Total")
    R = {"Demand": 15, "Hires": 16, "Layoffs": 17, "Workers on overtime": 18, "Workers": 19, "Production": 20, "Inventory at month end": 21, "Salaries ($)": 23, "Hire cost ($)": 24, "Layoff cost ($)": 25, "Overtime cost ($)": 26, "Inventory cost ($)": 27, "Total cost ($)": 28}
    for k, r in R.items(): lab(ws, r, 1, k, k in ("Total cost ($)",))
    for t in range(12):
        c = L(2 + t); pc = L(1 + t)
        inp(ws, 15, 2 + t, DEMAND[t])
        for r, k in ((16, 0), (17, 1), (18, 2)):
            y = ws.cell(r, 2 + t, int(x[k][t])); y.fill = PICK; y.font = F(bold=True)
        lab(ws, 19, 2 + t, f"=$B$11+{c}16-{c}17" if t == 0 else f"={pc}19+{c}16-{c}17")
        lab(ws, 20, 2 + t, f"=$B$10*({c}19+{c}18)")
        lab(ws, 21, 2 + t, f"=$B$12+{c}20-{c}15" if t == 0 else f"={pc}21+{c}20-{c}15")
        lab(ws, 23, 2 + t, f"=$B$5*{c}19"); lab(ws, 24, 2 + t, f"=$B$6*{c}16"); lab(ws, 25, 2 + t, f"=$B$7*{c}17"); lab(ws, 26, 2 + t, f"=$B$8*{c}18"); lab(ws, 27, 2 + t, f"=$B$4*{c}21")
        lab(ws, 28, 2 + t, f"=SUM({c}23:{c}27)")
    for r in list(range(15, 19)) + [20] + list(range(23, 29)): lab(ws, r, 14, f"=SUM(B{r}:M{r})", r == 28, "#,##0")
    lab(ws, 30, 1, "Solver setup", True)
    for k, t in enumerate(["Objective: minimize N28.", "Variables: B16:M18, whole numbers, not negative.", "Constraints: B21:M21 >= 0 (demand is met); B20:M20 <= B9 (capacity); B18:M18 <= B19:M19 (overtime).", "Method: Simplex LP."]): lab(ws, 31 + k, 1, t)
    ws.column_dimensions["A"].width = 40
    for j in range(2, 15): ws.column_dimensions[L(j)].width = 11
    s2 = wb.create_sheet("Strategies")
    for k, t in enumerate(["Strategy", "Salaries ($)", "Hires ($)", "Layoffs ($)", "Overtime ($)", "Inventory ($)", "Total ($)", "Against the mixed plan ($)"]): head(s2, 1, 1 + k, t)
    for i, m in enumerate(("mixed", "level", "chase")):
        r = 2 + i; lab(s2, r, 1, names[m][0])
        for j, k in enumerate(("Salaries", "Hires", "Layoffs", "Overtime", "Inventory")): inp(s2, r, 2 + j, int(res[m][2][k]), "#,##0")
        lab(s2, r, 7, f"=SUM(B{r}:F{r})", True, "#,##0"); lab(s2, r, 8, f"=G{r}-$G$2", fmt="#,##0")
    lab(s2, 6, 1, "Each row is the lowest-cost plan under the rules of that strategy. Source: plan.py (integer program).")
    s2.column_dimensions["A"].width = 34
    for c in "BCDEFGH": s2.column_dimensions[c].width = 16
    os.makedirs(f"projects/{slug}", exist_ok=True); wb.save(f"projects/{slug}/production_plan_model.xlsx")
    code = ('"""Seasonal production plan: integer program for workforce, overtime and inventory over 12 months."""\nimport numpy as np\nfrom scipy.optimize import milp, LinearConstraint, Bounds\n\n'
            'DEMAND = [4400, 4400, 6000, 8000, 6600, 11800, 13000, 11200, 10800, 7600, 6000, 5600]\nSALARY, HIRE, FIRE, OT, HOLD, PER, CAP, W0, I0 = 2400, 1800, 1200, 3300, 8, 40, 13000, 160, 240\n\n\n'
            + inspect.getsource(plan) + '\n\nif __name__ == "__main__":\n    for mode in ("mixed", "level", "chase"):\n        cost, x, parts = plan(mode)\n        print(mode, cost, {k: int(v) for k, v in parts.items()})\n        print("  workers", [int(v) for v in x[3]])\n')
    save(slug, html, {"plan.py": code})
    return {m: (res[m][0], {k: int(v) for k, v in res[m][2].items()}) for m in res}

if __name__ == "__main__":
    bid(); print("bid ok"); print(production()); print(rooms())
