"""Solve the two set-covering course projects, then write the page fragments,
the Excel models and the Python check scripts. Run from the repo root."""
import os, textwrap
from itertools import product
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L

NAVY, BLUE = "051C2C", "0000FF"
F = lambda size=10, **k: Font(name="Arial", size=size, **k)
HEAD = PatternFill("solid", fgColor=NAVY); PICK = PatternFill("solid", fgColor="FFFF00"); SOFT = PatternFill("solid", fgColor="F0F0F0")

def style(ws):
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None and not c.font.b and c.font.color is None: c.font = F()
def head(ws, r, c, v):
    x = ws.cell(r, c, v); x.font = F(bold=True, color="FFFFFF"); x.fill = HEAD; x.alignment = Alignment(horizontal="center", wrap_text=True); return x
def inp(ws, r, c, v):
    x = ws.cell(r, c, v); x.font = F(color=BLUE); return x
def lab(ws, r, c, v, bold=False):
    x = ws.cell(r, c, v); x.font = F(bold=bold); return x
def money(n): return f"${n:,.0f}"

# ---------------------------------------------------------------- fire stations
T = [[3,15,21,7,15,25],[11,5,13,16,12,21],[21,18,2,19,13,10],[8,21,20,4,8,17],[14,16,12,10,3,9],[22,23,9,18,8,2]]  # region x site, minutes
C = [400,50,300,450,250,350]  # $ thousand
def fire(limit, rules=True):
    best = None
    for x in product([0,1], repeat=6):
        if any(sum(x[j] for j in range(6) if T[i][j] <= limit) < 1 for i in range(6)): continue
        if rules and (x[0]+x[5] > 1 or x[3] > x[0] or x[4] != x[5]): continue
        c = sum(C[j]*x[j] for j in range(6))
        if best is None or c < best[0]: best = (c, x)
    return best

def fire_page():
    cost, x = fire(12); assert cost == 700 and x == (1,0,1,0,0,0) and fire(12, False)[0] == 700
    sites = [j+1 for j in range(6) if x[j]]
    serve = {i: min((T[i][j], j+1) for j in range(6) if x[j]) for i in range(6)}
    worst = max(v[0] for v in serve.values())
    steps, prev = [], "start"
    for t in range(1, 31):
        r = fire(t)
        key = r and r[0]
        if key != prev: steps.append([t, t, r])
        else: steps[-1][1] = t
        prev = key
    feas = [s for s in steps if s[2]]
    top = max(s[2][0] for s in feas)
    rows = ""
    for a, b, r in feas[:6]:
        rng = f"{a}" if a == b else f"{a} to {b}"
        on = " on" if a <= 12 <= b else ""
        open_ = ", ".join(str(j+1) for j in range(6) if r[1][j])
        rows += (f'<div class="cp-bar{on}"><span class="c">{rng} min</span><span class="t"><i style="width:{r[0]/top*100:.1f}%"></i></span>'
                 f'<span class="v">{money(r[0]*1000)}</span><span class="s">sites {open_}</span></div>')
    th = "".join(f'<th scope="col" class="n{" pick" if x[j] else ""}">Site {j+1}</th>' for j in range(6))
    body = ""
    for i in range(6):
        tds = ""
        for j in range(6):
            cls = "n" + (" pick" if x[j] else "") + (" ok" if T[i][j] <= 12 else "") + (" serve" if x[j] and serve[i][1] == j+1 else "")
            tds += f'<td class="{cls}">{T[i][j]}</td>'
        body += f'<tr><th scope="row">Region {i+1}</th>{tds}</tr>'
    costs = "".join(f'<td class="n{" pick" if x[j] else ""}">{money(C[j]*1000)}</td>' for j in range(6))
    tight = next(s for s in feas if s[1] < 12 and s[1] == 11)
    loose = next(s for s in feas if s[0] > 12)
    html = f"""<div class="cp-kpis">
  <div><p class="k">Lowest cost to cover all six regions</p><p class="v">{money(cost*1000)}</p><p class="s">sites {sites[0]} and {sites[1]}, out of 64 possible plans</p></div>
  <div><p class="k">Longest response time</p><p class="v">{worst} min</p><p class="s">region 5, exactly at the limit</p></div>
  <div><p class="k">Cost of one minute less</p><p class="v">+{money((tight[2][0]-cost)*1000)}</p><p class="s">an 11-minute limit needs three stations</p></div>
</div>
<section class="part"><h2>Sites 1 and 3 together reach every region within 12 minutes</h2>
  <div class="table-scroll"><table class="cp-grid">
    <caption>Travel time from each candidate site to each region, in minutes</caption>
    <thead><tr><th scope="col"></th>{th}</tr></thead>
    <tbody>{body}<tr class="cost"><th scope="row">Cost to open</th>{costs}</tr></tbody>
  </table></div>
  <p class="legend"><span class="k pick">Site</span> opened <span class="k serve">8</span> the station that serves the region <span class="k ok">12</span> inside the 12-minute limit</p>
</section>
<section class="part"><h2>The 12-minute limit sits just above a cost step: 11 minutes costs 64% more</h2>
  <div class="cp-bars" role="img" aria-label="Lowest cost for each response-time limit. 10 minutes: $1,200,000. 11 minutes: $1,150,000. 12 to 14 minutes: $700,000. 15 to 19 minutes: $600,000.">{rows}</div>
  <p class="cp-note">No plan covers all regions below 10 minutes. Each bar is the lowest-cost plan for that limit, with the three siting rules applied.</p>
</section>
<section class="part"><h2>The model</h2>
  <div class="cp-model">
    <div><h3>Decision</h3><p>Open or do not open each of the six candidate sites (six yes/no variables).</p></div>
    <div><h3>Objective</h3><p>The lowest total cost to open the stations.</p></div>
    <div><h3>Constraints</h3><p>Each region has at least one open station within the limit. Sites 1 and 6 are not opened together. Site 4 needs site 1. Sites 5 and 6 are opened together or not at all.</p></div>
  </div>
  <ul class="notes">
    <li>The three siting rules do not change the answer at 12 minutes. The plan without the rules is the same.</li>
    <li>Region 5 is 12 minutes from site 3, so the plan has no spare time there. A limit of 11 minutes adds site 4 and {money((tight[2][0]-cost)*1000)}.</li>
    <li>A limit of 15 minutes lets sites 5 and 6 replace sites 1 and 3 and saves {money((cost-loose[2][0])*1000)}.</li>
  </ul>
</section>"""
    open("data/course/fire-station-siting.html", "w", encoding="utf-8").write(html)

def fire_xlsx(path):
    wb = Workbook(); ws = wb.active; ws.title = "Model"
    lab(ws, 1, 1, "Fire station siting: set-covering model", True).font = F(bold=True, size=14)
    lab(ws, 2, 1, "Blue cells are inputs. Yellow cells are the decision. All other cells are formulas. Amounts are in $ thousand.")
    lab(ws, 4, 1, "Response-time limit (minutes)", True); inp(ws, 4, 2, 12)
    head(ws, 6, 1, "Travel time (minutes)")
    for j in range(6): head(ws, 6, 2+j, f"Site {j+1}")
    for i in range(6):
        lab(ws, 7+i, 1, f"Region {i+1}")
        for j in range(6): inp(ws, 7+i, 2+j, T[i][j])
    lab(ws, 13, 1, "Cost to open ($ thousand)", True)
    for j in range(6): inp(ws, 13, 2+j, C[j])
    lab(ws, 15, 1, "Open the site? (1 = yes)", True)
    x = fire(12)[1]
    for j in range(6):
        c = ws.cell(15, 2+j, x[j]); c.fill = PICK; c.font = F(bold=True)
    lab(ws, 16, 1, "Total cost ($ thousand)", True); c = ws.cell(16, 2, "=SUMPRODUCT(B13:G13,B15:G15)"); c.font = F(bold=True)
    head(ws, 18, 1, "Within the limit? (1 = yes)")
    for j in range(6): head(ws, 18, 2+j, f"Site {j+1}")
    head(ws, 18, 8, "Open stations in reach"); head(ws, 18, 9, "Needed"); head(ws, 18, 10, "Covered?")
    for i in range(6):
        r = 19+i; lab(ws, r, 1, f"Region {i+1}")
        for j in range(6): ws.cell(r, 2+j, f"=IF({L(2+j)}{7+i}<=$B$4,1,0)")
        ws.cell(r, 8, f"=SUMPRODUCT(B{r}:G{r},$B$15:$G$15)"); ws.cell(r, 9, 1); ws.cell(r, 10, f'=IF(H{r}>=I{r},"Yes","No")')
    head(ws, 26, 1, "Siting rules"); head(ws, 26, 8, "Value"); head(ws, 26, 9, "Limit"); head(ws, 26, 10, "Met?")
    lab(ws, 27, 1, "Sites 1 and 6 are not opened together (site 1 + site 6 <= 1)"); ws.cell(27, 8, "=B15+G15"); ws.cell(27, 9, 1); ws.cell(27, 10, '=IF(H27<=I27,"Yes","No")')
    lab(ws, 28, 1, "Site 4 needs site 1 (site 4 - site 1 <= 0)"); ws.cell(28, 8, "=E15-B15"); ws.cell(28, 9, 0); ws.cell(28, 10, '=IF(H28<=I28,"Yes","No")')
    lab(ws, 29, 1, "Sites 5 and 6 are opened together or not at all (site 5 - site 6 = 0)"); ws.cell(29, 8, "=F15-G15"); ws.cell(29, 9, 0); ws.cell(29, 10, '=IF(H29=I29,"Yes","No")')
    lab(ws, 31, 1, "Solver setup", True)
    for k, t in enumerate(["Objective: minimize B16.", "Variables: B15:G15, binary.", "Constraints: H19:H24 >= I19:I24; H27 <= I27; H28 <= I28; H29 = I29.", "Method: Simplex LP. To test a different service level, change B4 and run Solver again."]):
        lab(ws, 32+k, 1, t)
    ws.column_dimensions["A"].width = 62
    for j in range(2, 11): ws.column_dimensions[L(j)].width = 13
    s2 = wb.create_sheet("Cost by limit")
    head(s2, 1, 1, "Response-time limit (minutes)"); head(s2, 1, 2, "Lowest cost ($ thousand)"); head(s2, 1, 3, "Sites opened")
    r = 2
    for t in range(8, 26):
        res = fire(t)
        s2.cell(r, 1, t).font = F(); s2.cell(r, 2, res[0] if res else "No plan covers all regions").font = F(); s2.cell(r, 3, ", ".join(str(j+1) for j in range(6) if res[1][j]) if res else "").font = F(); r += 1
    lab(s2, r+1, 1, "Each row is one Solver run of the Model sheet with a different value in B4. The Python check script gives the same values.")
    s2.column_dimensions["A"].width = 30; s2.column_dimensions["B"].width = 28; s2.column_dimensions["C"].width = 20
    wb.save(path)

FIRE_PY = '''"""Fire station siting. Check of the Excel Solver model by full enumeration (64 plans)."""
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
'''

# ---------------------------------------------------------------- supplier bids
SUP = [1,2,3,1,4,2,5,6,3,7,2,5]
BID = [2050,350,1199,220,4639,199,1199,1350,350,2200,999,1700]
ITEMS = [("Brand A", "Large", 1000), ("Brand A", "Medium", 2500), ("Brand A", "Small", 4000), ("Brand B", "Large", 800), ("Brand B", "Medium", 1500), ("Brand B", "Small", 2500),
         ("Brand C", "Large", 400), ("Brand C", "Medium", 750), ("Brand C", "Small", 1200), ("Brand D", "Large", 100), ("Brand D", "Medium", 100), ("Brand D", "Small", 50)]
A = [[1,0,1,0,1,0,0,0,0,1,0,0],[1,0,0,0,1,0,0,0,0,1,0,0],[1,0,0,0,1,0,0,1,0,0,0,1],[0,0,1,0,1,0,0,0,0,1,0,0],[0,0,0,0,1,0,1,0,0,1,1,0],[0,0,0,0,1,0,1,1,0,0,1,1],
     [0,0,1,1,1,0,0,0,0,0,0,0],[0,0,0,0,1,0,0,0,1,0,0,0],[0,1,0,0,1,0,0,0,0,0,0,1],[0,0,1,1,1,0,0,0,0,0,0,0],[0,0,0,1,1,1,1,0,0,0,0,0],[0,0,0,1,1,1,1,1,0,0,0,1]]
def bids(extra=lambda x: True, need=None):
    need = need or [1]*12; best = None
    for x in product([0,1], repeat=12):
        if any(sum(a*v for a, v in zip(r, x)) < n for r, n in zip(A, need)): continue
        if not extra(x): continue
        c = sum(b*v for b, v in zip(BID, x))
        if best is None or c < best[0]: best = (c, [i+1 for i in range(12) if x[i]])
    return best
s1 = lambda x: 2050*x[0] + 220*x[3]
SCEN = [
    ("Lowest cost, no policy", "Each item is in at least one accepted bid.", lambda: bids()),
    ("A second source for one high-volume item", "Brand B medium is in at least two accepted bids.", lambda: bids(need=[1,1,1,1,2,1,1,1,1,1,1,1])),
    ("At least one local supplier", "At least one bid from supplier 6 or supplier 7.", lambda: bids(lambda x: x[7]+x[9] >= 1)),
    ("Business for three strategic partners", "At least one bid from supplier 1, one from supplier 3 and two from supplier 5.", lambda: bids(lambda x: x[0]+x[3] >= 1 and x[2]+x[8] >= 1 and x[6]+x[11] >= 2)),
    ("Supplier 1 sets a $500 minimum order", "Supplier 1 gets $500 or more, or nothing.", lambda: bids(lambda x: s1(x) == 0 or s1(x) >= 500)),
]

def bid_page():
    res = [(n, d, f()) for n, d, f in SCEN]
    base = res[0][2]; assert base == (4470, [4,9,10,12]) and res[4][2] == (4639, [5]) and res[3][2][0] == 5669 and res[2][2][0] == 4470
    pick = set(base[1]); top = max(r[2][0] for r in res)
    th = "".join(f'<th scope="col" class="n{" pick" if b+1 in pick else ""}">{b+1}</th>' for b in range(12))
    sup = "".join(f'<td class="n{" pick" if b+1 in pick else ""}">S{SUP[b]}</td>' for b in range(12))
    body = ""
    for i, (br, sz, q) in enumerate(ITEMS):
        tds = "".join(f'<td class="n{" pick" if b+1 in pick else ""}{" serve" if A[i][b] and b+1 in pick else (" ok" if A[i][b] else "")}">{"●" if A[i][b] else ""}</td>' for b in range(12))
        body += f'<tr><th scope="row">{br}, {sz.lower()} <span>{q:,}</span></th>{tds}</tr>'
    price = "".join(f'<td class="n{" pick" if b+1 in pick else ""}">{money(BID[b])}</td>' for b in range(12))
    rows = ""
    for k, (n, d, (c, bs)) in enumerate(res):
        diff = "base" if k == 0 else ("no extra cost" if c == base[0] else f"+{money(c-base[0])} (+{(c-base[0])/base[0]*100:.0f}%)")
        rows += (f'<div class="cp-bar wide{" on" if k == 0 else ""}"><span class="c"><b>{n}</b>{d}</span><span class="t"><i style="width:{c/top*100:.1f}%"></i></span>'
                 f'<span class="v">{money(c)}</span><span class="s">{diff}<br>bids {", ".join(map(str, bs))}</span></div>')
    second, partner, minimum = res[1][2], res[3][2], res[4][2]
    html = f"""<div class="cp-kpis">
  <div><p class="k">Lowest cost to buy all 12 items</p><p class="v">{money(base[0])}</p><p class="s">bids {", ".join(map(str, base[1]))}, from four suppliers</p></div>
  <div><p class="k">Saving against the one-supplier bundle</p><p class="v">{money(BID[4]-base[0])}</p><p class="s">{(BID[4]-base[0])/BID[4]*100:.1f}% below bid 5 at {money(BID[4])}</p></div>
  <div><p class="k">Cost of the strategic-partner policy</p><p class="v">+{money(partner[0]-base[0])}</p><p class="s">+{(partner[0]-base[0])/base[0]*100:.0f}%, the most expensive policy tested</p></div>
</div>
<section class="part"><h2>Four bids cover all 12 items, and only one small item is bought twice</h2>
  <div class="table-scroll"><table class="cp-grid bids">
    <caption>Items in each bid. Each bid is all-or-nothing at one price.</caption>
    <thead><tr><th scope="col">Bid</th>{th}</tr></thead>
    <tbody><tr class="cost"><th scope="row">Supplier</th>{sup}</tr>{body}<tr class="cost"><th scope="row">Bid price</th>{price}</tr></tbody>
  </table></div>
  <p class="legend"><span class="k pick">4</span> accepted bid <span class="k serve">●</span> item bought through this bid <span class="k ok">●</span> item offered, bid not accepted</p>
</section>
<section class="part"><h2>A local supplier is free, but the partner policy adds 27% to the cost</h2>
  <div class="cp-bars" role="img" aria-label="Lowest cost under each sourcing policy.">{rows}</div>
</section>
<section class="part"><h2>The model</h2>
  <div class="cp-model">
    <div><h3>Decision</h3><p>Accept or reject each of the 12 bids from 7 suppliers (12 yes/no variables).</p></div>
    <div><h3>Objective</h3><p>The lowest total price of the accepted bids.</p></div>
    <div><h3>Constraints</h3><p>Each of the 12 items is in at least one accepted bid. Each sourcing policy adds one or more linear constraints.</p></div>
  </div>
  <ul class="notes">
    <li>The local-supplier policy has no cost, because the lowest-cost plan already has a bid from supplier 7.</li>
    <li>A second source for Brand B medium costs {money(second[0]-base[0])} more ({(second[0]-base[0])/base[0]*100:.0f}%).</li>
    <li>With a $500 minimum order for supplier 1, the $220 bid from that supplier is not available alone. The one-supplier bundle then has the lowest cost, at {money(minimum[0])}.</li>
    <li>The minimum-order rule needs one more yes/no variable: do business with supplier 1 or not.</li>
  </ul>
</section>"""
    open("data/course/supplier-bid-selection.html", "w", encoding="utf-8").write(html)
    return res

def bid_xlsx(path, res):
    wb = Workbook(); ws = wb.active; ws.title = "Model"
    lab(ws, 1, 1, "Supplier bid selection: set-covering model", True).font = F(bold=True, size=14)
    lab(ws, 2, 1, "Blue cells are inputs. Yellow cells are the decision. All other cells are formulas. Brand names are replaced with letters.")
    head(ws, 4, 1, "Bid")
    for b in range(12): head(ws, 4, 3+b, b+1)
    lab(ws, 5, 1, "Supplier", True)
    for b in range(12): inp(ws, 5, 3+b, SUP[b])
    head(ws, 6, 1, "Item"); head(ws, 6, 2, "Quantity")
    for b in range(12): head(ws, 6, 3+b, "In bid?")
    head(ws, 6, 15, "Accepted bids with the item"); head(ws, 6, 16, "Needed"); head(ws, 6, 17, "Covered?")
    for i, (br, sz, q) in enumerate(ITEMS):
        r = 7+i; lab(ws, r, 1, f"{br}, {sz.lower()}"); inp(ws, r, 2, q)
        for b in range(12): inp(ws, r, 3+b, A[i][b])
        ws.cell(r, 15, f"=SUMPRODUCT(C{r}:N{r},$C$21:$N$21)"); inp(ws, r, 16, 1); ws.cell(r, 17, f'=IF(O{r}>=P{r},"Yes","No")')
    lab(ws, 19, 1, "Bid price ($)", True)
    for b in range(12): inp(ws, 19, 3+b, BID[b])
    lab(ws, 21, 1, "Accept the bid? (1 = yes)", True)
    for b in range(12):
        c = ws.cell(21, 3+b, 1 if b+1 in res[0][2][1] else 0); c.fill = PICK; c.font = F(bold=True)
    lab(ws, 22, 1, "Total cost ($)", True); ws.cell(22, 3, "=SUMPRODUCT(C19:N19,C21:N21)").font = F(bold=True)
    head(ws, 24, 1, "Sourcing policies (add one at a time as a Solver constraint)"); head(ws, 24, 15, "Value"); head(ws, 24, 16, "Limit")
    pol = [("Second source: change P11 (Brand B medium) from 1 to 2", "=O11", ">= 2"),
           ("Local supplier: bids from supplier 6 or 7", '=SUMPRODUCT((C5:N5>=6)*C21:N21)', ">= 1"),
           ("Strategic partner, supplier 1: accepted bids", '=SUMPRODUCT((C5:N5=1)*C21:N21)', ">= 1"),
           ("Strategic partner, supplier 3: accepted bids", '=SUMPRODUCT((C5:N5=3)*C21:N21)', ">= 1"),
           ("Strategic partner, supplier 5: accepted bids", '=SUMPRODUCT((C5:N5=5)*C21:N21)', ">= 2"),
           ("Minimum order: total price of accepted bids from supplier 1 ($)", '=SUMPRODUCT((C5:N5=1)*C19:N19*C21:N21)', "0, or >= 500")]
    for k, (t, f, lim) in enumerate(pol):
        lab(ws, 25+k, 1, t); ws.cell(25+k, 15, f); ws.cell(25+k, 16, lim)
    lab(ws, 32, 1, "Solver setup", True)
    for k, t in enumerate(["Objective: minimize C22.", "Variables: C21:N21, binary.", "Constraints: O7:O18 >= P7:P18, plus the policy under test.",
                           "Minimum order: add a binary cell y. Constraints: O30 >= 500*y, C21 <= y, F21 <= y.", "Method: Simplex LP."]):
        lab(ws, 33+k, 1, t)
    ws.column_dimensions["A"].width = 60; ws.column_dimensions["B"].width = 10
    for j in range(3, 15): ws.column_dimensions[L(j)].width = 8
    for j in (15, 16, 17): ws.column_dimensions[L(j)].width = 16
    s2 = wb.create_sheet("Policies")
    for k, t in enumerate(["Policy", "Constraint", "Lowest cost ($)", "Accepted bids", "Change from base ($)"]): head(s2, 1, 1+k, t)
    for k, (n, d, (c, bs)) in enumerate(res):
        r = 2+k
        lab(s2, r, 1, n); lab(s2, r, 2, d); inp(s2, r, 3, c); lab(s2, r, 4, ", ".join(map(str, bs))); s2.cell(r, 5, f"=C{r}-$C$2").font = F()
    lab(s2, 8, 1, "Each cost in column C is the result of one Solver run of the Model sheet. The Python check script gives the same values.")
    for col, w in zip("ABCDE", (40, 70, 16, 18, 20)): s2.column_dimensions[col].width = w
    wb.save(path)

BID_PY = '''"""Supplier bid selection. Check of the Excel Solver model by full enumeration (4,096 plans)."""
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
'''

if __name__ == "__main__":
    for slug in ("fire-station-siting", "supplier-bid-selection"): os.makedirs(f"projects/{slug}", exist_ok=True)
    fire_page(); fire_xlsx("projects/fire-station-siting/fire_station_model.xlsx"); open("projects/fire-station-siting/check_model.py", "w").write(FIRE_PY)
    res = bid_page(); bid_xlsx("projects/supplier-bid-selection/bid_selection_model.xlsx", res); open("projects/supplier-bid-selection/check_model.py", "w").write(BID_PY)
    for n, d, r in res: print(n, r)
    for t in (10, 11, 12, 15, 20): print(t, fire(t))
