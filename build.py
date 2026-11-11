"""Build the static site from data/projects.json and data/resume.json.

Run from the repository root:  python3 build.py
The script writes index.html and the folders projects/, resume/, skills/ and contact/.
To add a project, add one entry to data/projects.json and run the script again.
"""
import json
import os
from html import escape as e

P = json.load(open("data/projects.json", encoding="utf-8"))
R = json.load(open("data/resume.json", encoding="utf-8"))
TOOLS = {t["id"]: t["name"] for t in P["tools"]}
PROJECTS = P["projects"]
PAGES = [p for p in PROJECTS if p.get("slug")]
CASES = [p for p in PROJECTS if p["type"] == "case"]
NAV = [("Home", "/"), ("Projects", "/projects/"), ("Resume", "/resume/"), ("Skills", "/skills/"), ("Contact", "/contact/")]


def url(p):
    return f"/projects/{p['slug']}/"


def ico(tool):
    return f'<i class="ico" style="--i:url(/assets/icons/{tool}.svg)" aria-hidden="true"></i>'


def tools(ids):
    if not ids:
        return ""
    return '<div class="tools">' + "".join(f'<span class="tool">{ico(t)}{e(TOOLS[t])}</span>' for t in ids) + "</div>"


def page(path, title, desc, current, body):
    mark = ' aria-current="page"'
    nav = "".join(f'<li><a href="{href}"{mark if href == current else ""}>{name}</a></li>' for name, href in NAV)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="stylesheet" href="/assets/site.css">
<script>document.documentElement.classList.add('js');</script>
</head>
<body>
<nav class="bar" aria-label="Main">
  <div class="wrap">
    <a class="home" href="/">{e(R['name'])}</a>
    <ul>{nav}</ul>
  </div>
</nav>
{body}
<footer>
  <div class="wrap">
    <p class="links"><a href="mailto:{e(R['email'])}">{e(R['email'])}</a><a href="{e(R['linkedin'])}">LinkedIn</a><a href="{e(R['github'])}">GitHub</a></p>
    <p class="note">The case studies use public data sets, not data from an employer or a client.</p>
  </div>
</footer>
<script src="/assets/site.js"></script>
</body>
</html>
"""
    out = os.path.join(path.strip("/"), "index.html") if path.strip("/") else "index.html"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)


def kw(p):
    return f'<p class="kw">{e(" · ".join(p["kw"]))}</p>' if p.get("kw") else ""


def home():
    hl = [p for p in PROJECTS if p.get("highlight")]
    proofs = "".join(
        f'<li><a href="/projects/#type=work"><span class="name">{e(p["org"])}, {e(p["period"])}</span><span class="num">{e(p["highlight"][0])}</span>'
        f'<span class="what">{e(p["highlight"][1])}</span></a></li>'
        for p in hl
    )
    cases = "".join(
        f'<a class="card" href="{url(p)}"><span class="kw">{e(" · ".join(p.get("kw", [])))}</span><span class="name">{e(p["title"])}</span><span class="num">{e(p["num"])}</span>'
        f'<span class="what">{e(p["what"])}</span><span class="go">Open the case</span></a>'
        for p in CASES
    )
    strip = "".join(f'<a href="/skills/#{t}">{ico(t)}{e(n)}</a>' for t, n in TOOLS.items())
    jobs = "".join(
        f'<li><span class="when">{e(j["period"])}</span><span class="org">{e(j["org"])}</span>'
        f'<span class="did">{e(", ".join(r["title"] for r in j["roles"]))}</span></li>'
        for j in R["experience"]
    )
    method = "".join(f'<li><b>{e(a)}</b><span>{e(t)}</span></li>' for a, t in R["method"])
    body = f"""<header class="lead">
  <div class="wrap">
    <p class="role">{e(R['role'])}</p>
    <h1>{e(R['claim'])}</h1>
    <p class="background">{" ".join(e(s) for s in R.get('story', [R['background']]))}</p>
    <p class="actions"><a class="btn solid" href="/projects/">See all projects</a><a class="btn" href="/resume/">Read the resume</a></p>
    <p class="proofs-head">Results from work experience</p>
    <ul class="proofs">{proofs}</ul>
  </div>
</header>
<main>
  <section class="section">
    <div class="wrap">
      <h2>How I work, from the question to the launch</h2>
      <ol class="method">{method}</ol>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>Four case studies that I built on my own, with public data</h2>
      <p class="lede">They show how I work on a credit, a fraud, a marketing and an ATM network decision. They are not client or employer work.</p>
      <div class="cards c2">{cases}</div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>Ten years of work across audit, business operations and strategy</h2>
      <ul class="timeline">{jobs}</ul>
      <p class="more"><a href="/resume/">Full resume</a></p>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <h2>The tools I work with</h2>
      <div class="toolstrip">{strip}</div>
      <p class="more"><a href="/skills/">Projects by tool</a></p>
    </div>
  </section>
</main>"""
    page("/", f"{R['name']}: strategy and business operations", R["claim"], "/", body)


IND = {x["id"]: x["name"] for x in P.get("industries", [])}
TASK = {x["id"]: x["name"] for x in P.get("tasks", [])}


TYPE = {x["id"]: x for x in P["types"]}


def tags(p):
    out = f'<span class="tag type {p["type"]}">{e(TYPE[p["type"]]["tag"])}</span>' 
    if p.get("industry"):
        out += f'<span class="tag ind">{e(IND[p["industry"]])}</span>'
    for t in p.get("tasks", []):
        out += f'<span class="tag">{e(TASK[t])}</span>'
    return f'<p class="tags">{out}</p>' if out else ""


def data_attrs(p):
    return f'data-type="{p["type"]}" data-tools="{" ".join(p["tools"])}" data-industry="{p.get("industry", "")}" data-tasks="{" ".join(p.get("tasks", []))}"'


def project_row(p):
    head = f'<a href="{url(p)}">{e(p["title"])}</a>' if p.get("slug") else e(p["title"])
    meta = f'<b>{e(p["org"])}</b>{e(p.get("period", ""))}' if p.get("org") else "<b>Practice set</b>"
    return (
        f'<li class="prow" {data_attrs(p)}><div class="meta">{meta}</div>'
        f'<div>{kw(p)}<h3>{head}</h3><p>{e(p["result"])}</p>{tags(p)}</div>{tools(p["tools"]) or "<div></div>"}</li>'
    )


def matrix():
    tagged = [p for p in PROJECTS if p.get("industry")]
    head = "".join(f'<th scope="col"><button type="button" data-f="industry" data-v="{i}">{e(n)}</button></th>' for i, n in IND.items())
    rows = ""
    for t, tn in TASK.items():
        cells = ""
        for i in IND:
            inside = [p for p in tagged if p["industry"] == i and t in p["tasks"]]
            n = len(inside)
            kind = "" if any(p["type"] == "work" for p in inside) else " self"
            cells += f'<td><button type="button" class="cell{kind}" data-i="{i}" data-t="{t}" aria-label="{n} projects: {e(tn)}, {e(IND[i])}">{n}</button></td>' if n else '<td class="none">–</td>'
        total = len([p for p in tagged if t in p["tasks"]])
        rows += f'<tr><th scope="row"><button type="button" data-f="task" data-v="{t}">{e(tn)}</button></th>{cells}<td class="tot">{total}</td></tr>'
    foot = "".join(f'<td class="tot">{len([p for p in tagged if p["industry"] == i])}</td>' for i in IND)
    return f"""<div class="table-scroll"><table class="matrix">
      <thead><tr><th scope="col" class="corner">Task / Industry</th>{head}<th scope="col" class="tot">All</th></tr></thead>
      <tbody>{rows}<tr><th scope="row" class="tot">All</th>{foot}<td class="tot">{len(tagged)}</td></tr></tbody></table></div>
    <p class="legend"><span class="k work">3</span> work experience <span class="k self">1</span> self-built case study or course project</p>"""


def projects_index():
    used = [t for t in TOOLS if any(t in p["tools"] for p in PROJECTS)]
    buttons = "".join(f'<button type="button" data-f="tool" data-v="{t}" aria-pressed="false">{ico(t)}{e(TOOLS[t])}</button>' for t in used)
    groups = ""
    for t in P["types"]:
        items = [p for p in PROJECTS if p["type"] == t["id"]]
        if not items:
            continue
        if t["id"] == "case":
            inner = '<div class="cards">' + "".join(
                f'<a class="card" href="{url(p)}" {data_attrs(p)}><span class="name">{e(p["title"])}</span>'
                f'<span class="num">{e(p["num"])}</span><span class="what">{e(p["what"])}</span>'
                f'{tags(p)}{tools(p["tools"])}<span class="go">Open the case</span></a>'
                for p in items
            ) + "</div>"
        else:
            inner = '<ul class="rows">' + "".join(project_row(p) for p in items) + "</ul>"
        note = f'<p class="note">{e(t["note"])}</p>' if t["note"] else ""
        groups += f'<section class="group" id="{t["id"]}"><div class="ghead"><h2>{e(t["name"])}</h2><span class="gcount">{len(items)} project{"s" if len(items) > 1 else ""}</span></div>{note}{inner}</section>'
    typebtn = "".join(f'<button type="button" data-f="type" data-v="{t["id"]}" aria-pressed="false">{e(t["name"].split(",")[0])}</button>' for t in P["types"] if any(p["type"] == t["id"] for p in PROJECTS))
    taskopt = "".join(f'<option value="{k}">{e(v)}</option>' for k, v in TASK.items())
    indopt = "".join(f'<option value="{k}">{e(v)}</option>' for k, v in IND.items())
    body = f"""<main>
  <div class="pagehead"><div class="wrap">
    <h1>Projects</h1>
    <p class="sub">Work experience, self-built case studies and course projects, by task and industry.</p>
  </div></div>
  <div class="body"><div class="wrap">
    <h2 class="zone">Projects by task and industry</h2>
    <p class="howto">Select a number, a task or an industry in the table to see the projects.</p>
    {matrix()}
    <div class="filter" role="group" aria-label="Filter projects">
      <p class="fhead">Filter projects</p>
      <div class="frow"><span class="label">Type</span>{typebtn}</div>
      <div class="frow"><span class="label">Task</span><select data-s="task" aria-label="Task"><option value="">All tasks</option>{taskopt}</select><span class="label gap">Industry</span><select data-s="industry" aria-label="Industry"><option value="">All industries</option>{indopt}</select></div>
      <div class="frow"><span class="label">Tool</span>{buttons}</div>
    </div>
    <div class="found" id="found" hidden><h2 aria-live="polite"></h2><button type="button" class="clear">Show all projects</button></div>
    {groups}
    <p class="empty">No project matches these filters.</p>
  </div></div>
</main>"""
    page("/projects/", f"Projects: {R['name']}", "Projects by industry, task and tool.", "/projects/", body)


CHART = """<div class="exhibit">
  <p class="title">The 2015 loans lost money under the current policy; the new cutoff recovers $7.1M</p>
  <p class="unit">Realized NPV, $M</p>
  <div class="build" id="chart" role="img" aria-label="Bar chart. Loans from 2013 to 2014 under the current policy: plus 71.7 million dollars. Loans from 2015 under the current policy: minus 32.9 million dollars. Gain from the new cutoff on the 2015 loans: plus 7.1 million dollars.">
    <div class="row"><div class="label">Loans from 2013–2014, current policy</div><div class="track"><div class="fill pos context" style="width:59.75%"></div><div class="value inside" style="right:6.92%">+$71.7M</div></div></div>
    <div class="row"><div class="label">Loans from 2015, current policy</div><div class="track"><div class="fill neg loss" style="width:27.42%"></div><div class="value is-loss" style="left:33.33%">–$32.9M</div></div></div>
    <div class="row"><div class="label">Loans from 2015, gain from the new cutoff</div><div class="track"><div class="fill pos point" style="width:5.92%"></div><div class="value is-point" style="left:39.25%">+$7.1M</div></div></div>
  </div>
  <p class="source">Source: Lending Club public loan data; analysis. The gain is measured against the current policy on the same 2015 loans.</p>
</div>"""


def tree_node(n):
    sub = f'<span>{e(n["s"])}</span>' if n.get("s") else ""
    box = f'<div class="node {n.get("k", "")}"><b>{e(n["t"])}</b>{sub}</div>'
    find = ""
    if n.get("q"):
        find = f'<div class="find"><p class="q">{e(n["q"])}</p><p class="a"><b>{e(n["a"])}.</b> {e(n["ev"])}</p></div>'
    kids = ""
    if n.get("c"):
        kids = "<ul>" + "".join(f"<li>{tree_node(c)}</li>" for c in n["c"]) + "</ul>"
    return box + find + kids


SWAP = """<div class="swap" role="img" aria-label="Diagram. Both policies approve the same number of the 2015 applicants. The scorecard drops 24,426 loans with a default rate of 25.1% and adds 24,426 loans with a default rate of 23.6%.">
  <div class="sw-flow"><span>Learn: loans from 2013–2014</span><i></i><span>Test: loans from 2015, never seen by the model</span></div>
  <div class="sw-grid">
    <p class="sw-row">Current policy</p><div class="sw on"></div><div class="sw on"></div><div class="sw off"></div><div class="sw off"></div>
    <p class="sw-row">Scorecard</p><div class="sw on"></div><div class="sw off drop"></div><div class="sw add"></div><div class="sw off"></div>
    <p class="sw-row"></p>
    <p class="sw-lab">Approved by both</p>
    <p class="sw-lab"><b>Dropped by the scorecard</b>24,426 loans<br>default rate 25.1%</p>
    <p class="sw-lab add"><b>Added by the scorecard</b>24,426 loans<br>default rate 23.6%</p>
    <p class="sw-lab">Declined by both</p>
  </div>
  <p class="sw-note">The 2015 applicants, from low risk to high risk. Not to scale. Filled = approved. The swap adds $8.3M of realized NPV.</p>
</div>"""


def evaluation(p):
    f = f"data/briefs/{p['slug']}.json"
    if not os.path.exists(f):
        return []
    ev = json.load(open(f, encoding="utf-8")).get("evaluation", [])
    over = p.get("evaluation", [])
    return [over[i] if i < len(over) and over[i] else r for i, r in enumerate(ev)]


def deliverables(p, has_deck, has_brief):
    items = []
    if has_deck:
        items.append(("deck", "Board deck", "For leadership", "#deck"))
    if has_brief:
        items.append(("doc", "Technical document", "Method, results and model code" if p.get("code") else "Method, results, notebook and files", "brief/"))
    cards = "".join(
        f'<a class="dl" href="{href}">{ico(i)}<span><b>{e(t)}</b><em>{e(s)}</em></span></a>' for i, t, s, href in items
    )
    return f'<div class="dls">{cards}</div>' if cards else ""


def rec_slide(p):
    acts = "".join(f'<li class="{"main" if i == 0 else ""}"><b>{e(r[0])}</b><span>{e(r[1])}</span></li>' for i, r in enumerate(p["recs"]))
    risks = "".join(f"<tr><td>{e(r[0])}</td><td>{e(r[1])}</td></tr>" for r in p.get("risks", []))
    return f"""<section class="slide" data-part="Recommendation">
  <h3>{e(p['rec_title'])}</h3>
  <div class="s-body halves">
    <div><p class="s-bar">Actions</p><ol class="s-acts">{acts}</ol></div>
    <div><p class="s-bar">Risks and controls</p><table class="s-risks"><tbody>{risks}</tbody></table></div>
  </div>
  <p class="s-src">Source: analysis. Public data; illustrative results.</p>
</section>"""


def case_page(p, crumb):
    slug = p["slug"]
    deck_file = f"data/decks/{slug}.html"
    has_deck, has_brief = os.path.exists(deck_file), os.path.exists(f"data/briefs/{slug}.html")
    parts = ""
    if has_deck:
        deck = open(deck_file, encoding="utf-8").read() + (rec_slide(p) if p.get("recs") else "")
        n = deck.count('<section class="slide"')
        parts += f"""<section id="deck">
      <div class="deck">
        <div class="stage" tabindex="0" aria-roledescription="slide deck" aria-label="Board deck, {n} slides. Use the arrow keys to change slide.">{deck}</div>
        <div class="deckbar"><button type="button" class="prev" aria-label="Previous slide">Previous</button><span class="count" aria-live="polite">1 / {n}</span><button type="button" class="next" aria-label="Next slide">Next</button><button type="button" class="full">Full screen</button></div>
      </div></section>"""
    if p.get("tree"):
        parts += f"""<section class="part" id="tree"><h2>{e(p['tree_h'])}</h2>
      <div class="ltree-scroll"><ul class="ltree"><li>{tree_node(p['tree'])}</li></ul></div>
      <p class="legend"><span class="k lever">Lever</span> what the recommendation changes <span class="k limit">Limit</span> what must not get worse <span class="k fixed">Fixed</span> outside the decision</p></section>"""
    if p.get("method", {}).get("viz"):
        parts += f'<section class="part" id="method"><h2>{e(p["method"]["h"])}</h2>{SWAP}</section>'
    scqa, sub = "", f'<p class="sub result">{e(p["result"])}</p>'
    if p.get("scqa"):
        # The Answer row gives the result, so the page head does not repeat it.
        rows = "".join(
            f'<tr class="{r[0].lower()}"><th scope="row">{e(r[0])}<span>{e(r[1])}</span></th><td>{r[2]}</td></tr>' for r in p["scqa"]
        )
        scqa, sub = f'<table class="scqa cp-scqa case-scqa">{rows}</table>', ""
    return f"""<main>
  <div class="pagehead"><div class="wrap">{crumb}
    {kw(p)}
    <h1>{e(p['title'])}</h1>
    {sub}
    <div class="case-facts"><p class="facts"><b>Self-built case study.</b> {e(p['data'])}. Not client or employer work.</p>{tools(p['tools'])}</div>
    {deliverables(p, has_deck, has_brief)}
  </div></div>
  <div class="body"><div class="wrap">
    {scqa}
    {parts}
    {pager(p)}
  </div></div>
</main>"""


def brief_page(p):
    slug = p["slug"]
    brief_file = f"data/briefs/{slug}.html"
    if not os.path.exists(brief_file):
        return
    crumb = f'<p class="crumb"><a href="/projects/">Projects</a> / <a href="{url(p)}">{e(p["title"])}</a> / Technical document</p>'
    parts = ""
    if p.get("method"):
        mt = p["method"]
        st = "".join(f'<li><h3>{e(x[0])}</h3><p>{e(x[1])}</p></li>' for x in mt["steps"])
        notes = "".join(f"<li>{e(x)}</li>" for x in mt["notes"])
        viz = SWAP if mt.get("viz") else ""
        parts += f'<section class="part first"><h2>{e(mt["h"])}</h2>{viz}<ol class="steps3">{st}</ol><ul class="notes">{notes}</ul></section>'
    ev = evaluation(p)
    if ev:
        trs = "".join(
            f'<tr><td><b>{e(r[0])}</b></td><td>{e(r[1])}</td><td>{e(r[2])}</td><td>{e(r[3])}</td><td class="{"yes" if r[4] == "Yes" else "no"}"><b>{e(r[4])}</b></td></tr>'
            for r in ev
        )
        eval_h = p.get("eval_h", "Five tests, with rules set before the analysis")
        eval_lede = p.get("eval_lede", "In the notebook, the champion is the current policy and the challenger is the new policy.")
        parts += f"""<section class="part"><h2>{e(eval_h)}</h2>
      <p class="lede">{e(eval_lede)}</p>
      <div class="table-scroll"><table class="eval"><thead><tr><th scope="col">Test</th><th scope="col">Measure</th><th scope="col">Result</th><th scope="col">Rule</th><th scope="col">Pass</th></tr></thead><tbody>{trs}</tbody></table></div></section>"""
    brief = open(brief_file, encoding="utf-8").read().replace('href="notebook/', 'href="../notebook/')
    parts += f'<section class="part"><h2>Results</h2><div class="brief">{brief}</div></section>'
    if p.get("uses"):
        us = "".join(f'<tr><td><b>{e(x[0])}</b></td><td>{e(x[1])}</td></tr>' for x in p["uses"])
        parts += f'<section class="part"><h2>What each tool does in this case</h2><div class="table-scroll"><table><tbody>{us}</tbody></table></div></section>'
    xl = f'<a class="dl" href="../{e(p["excel"])}">{ico("excel")}<span><b>P&amp;L model</b><em>Excel workbook</em></span></a>' if p.get("excel") else ""
    nb = f'<a class="dl" href="../notebook/">{ico("notebook")}<span><b>Full notebook</b><em>Every step, with code</em></span></a>'
    if p.get("code"):
        nb = f'<a class="dl" href="{e(p["code"])}">{ico("notebook")}<span><b>Model code</b><em>Python, on GitHub</em></span></a>'
    body = f"""<main>
  <div class="pagehead"><div class="wrap">{crumb}
    <h1>{e(p['title'])}: technical document</h1>
    <div class="dls">{nb}{xl}<a class="dl" href="{url(p)}#deck">{ico("deck")}<span><b>Board deck</b><em>For leadership</em></span></a></div>
  </div></div>
  <div class="body"><div class="wrap">{parts}</div></div>
</main>"""
    page(url(p) + "brief/", f"{p['title']}: technical document", p["result"], "/projects/", body)


def course_page(p, crumb):
    tree = ""
    if p.get("tree"):
        tree = f'''<section class="part cp-tree"><h2>{e(p['tree_h'])}</h2>
      <div class="ltree-scroll"><ul class="ltree"><li>{tree_node(p['tree'])}</li></ul></div>
      <p class="legend"><span class="k lever">Lever</span> what the decision changes <span class="k limit">Limit</span> what the answer must respect <span class="k fixed">Fixed</span> outside the decision</p></section>'''
    frag = open(f"data/course/{p['slug']}.html", encoding="utf-8").read()
    cards = "".join(
        f'<a class="dl" href="{e(href)}">{ico(i)}<span><b>{e(t)}</b><em>{e(s)}</em></span></a>' for i, t, s, href in p.get("files", [])
    )
    return f"""<main>
  <div class="pagehead"><div class="wrap">{crumb}
    <h1>{e(p['title'])}</h1>
    <div class="case-facts"><p class="facts"><b>Course project, Michigan Ross MBA.</b> {e(p['method'])}. Not client or employer work.</p>{tools(p['tools'])}</div>
    {f'<div class="dls">{cards}</div>' if cards else ""}
  </div></div>
  <div class="body"><div class="wrap cp">
    <table class="scqa cp-scqa">
      <tr><th scope="row">Situation</th><td>{e(p['scq'][0])}</td></tr>
      <tr><th scope="row">Complication</th><td>{e(p['scq'][1])}</td></tr>
      <tr class="question"><th scope="row">Question</th><td>{e(p['scq'][2])}</td></tr>
      <tr class="answer"><th scope="row">Answer</th><td>{e(p['result'])}</td></tr>
    </table>
    {tree}
    {frag}
    {pager(p)}
  </div></div>
</main>"""


def pager(p):
    i = PAGES.index(p)
    prev = PAGES[i - 1] if i > 0 else None
    nxt = PAGES[i + 1] if i < len(PAGES) - 1 else None
    a = f'<a href="{url(prev)}"><span>Previous project</span><b>{e(prev["title"])}</b></a>' if prev else "<span></span>"
    b = f'<a class="next" href="{url(nxt)}"><span>Next project</span><b>{e(nxt["title"])}</b></a>' if nxt else "<span></span>"
    return f'<nav class="pager" aria-label="More projects">{a}{b}</nav>'


def project_pages():
    for p in PAGES:
        crumb = f'<p class="crumb"><a href="/projects/">Projects</a> / {e(p["title"])}</p>'
        if p["type"] == "case":
            body = case_page(p, crumb)
            brief_page(p)
        elif p["type"] == "course":
            body = course_page(p, crumb)
        else:
            rows = "".join(
                f'<tr><td><a href="{e(p["repo"])}/{g[2]}">{e(g[0])}</a></td><td class="n">{g[1]}</td></tr>' for g in p["groups"]
            )
            total = sum(g[1] for g in p["groups"])
            body = f"""<main>
  <div class="pagehead"><div class="wrap">{crumb}
    <h1>{e(p['headline'])}</h1>
  </div></div>
  <div class="body"><div class="wrap">
    <div class="case-head"><p class="facts">Each solution is one file, sorted by topic group.</p>{tools(p['tools'])}</div>
    <div class="table-scroll"><table>
      <thead><tr><th scope="col">Topic group</th><th scope="col" class="n">Problems solved</th></tr></thead>
      <tbody>{rows}<tr><td><b>Total</b></td><td class="n"><b>{total}</b></td></tr></tbody>
    </table></div>
    <p style="margin-top:24px"><a href="{e(p['repo'])}">Open the solutions on GitHub</a></p>
    {pager(p)}
  </div></div>
</main>"""
        page(url(p), f"{p['title']}: {R['name']}", p["result"], "/projects/", body)


def resume():
    jobs = ""
    for j in R["experience"]:
        roles = ""
        for r in j["roles"]:
            note = f' <span>({e(r["note"])})</span>' if r.get("note") else ""
            roles += f'<p class="title">{e(r["title"])}{note}</p><ul>' + "".join(f"<li>{e(b)}</li>" for b in r["bullets"]) + "</ul>"
        jobs += (
            f'<div class="job"><div class="meta"><b>{e(j["period"])}</b>{e(j["place"])}</div>'
            f'<div><h3>{e(j["org"])}</h3><p class="about">{e(j["about"])}</p>{roles}</div></div>'
        )
    edu = ""
    for s in R["education"]:
        edu += (
            f'<div class="job"><div class="meta"><b>{e(s["degree"].split(", ")[-1])}</b>{e(s["place"])}</div>'
            f'<div><h3>{e(s["school"])}</h3><p class="title">{e(s["degree"].rsplit(", ", 1)[0])}</p><ul>'
            + "".join(f"<li>{e(b)}</li>" for b in s["bullets"]) + "</ul></div></div>"
        )
    certs = "".join(f"<li>{e(c)}</li>" for c in R["certifications"])
    body = f"""<main>
  <div class="pagehead"><div class="wrap">
    <h1>Resume</h1>
    <p class="sub">{e(R['background'])}</p>
  </div></div>
  <div class="body"><div class="wrap cv">
    <h2>Experience</h2>{jobs}
    <h2>Education</h2>{edu}
    <h2>Certifications</h2><ul class="plainlist">{certs}</ul>
    <h2>Tools</h2><div style="margin-top:20px">{tools([t for t in TOOLS if t != "r"])}</div>
    <p style="margin-top:14px;font-size:15px;color:var(--muted)">Also: {e(R.get("other_tools", ""))}</p>
  </div></div>
</main>"""
    page("/resume/", f"Resume: {R['name']}", R["background"], "/resume/", body)


def skills():
    rows, rest = "", []
    for t, name in TOOLS.items():
        items = [p for p in PROJECTS if t in p["tools"]]
        if not items:
            rest.append(t)
            continue
        groups, mix = "", []
        for ty in P["types"]:
            sub = [p for p in items if p["type"] == ty["id"]]
            if not sub:
                continue
            short = ty["name"].split(",")[0].lower()
            mix.append(f"{len(sub)} {short}")
            lis = ""
            for p in sub:
                label = f'<a href="{url(p)}">{e(p["title"])}</a>' if p.get("slug") else e(p["title"])
                where = f' <span>({e(p["org"])})</span>' if ty["id"] == "work" and p.get("org") else ""
                lis += f"<li>{label}{where}</li>"
            groups += f'<h3>{e(ty["name"].split(",")[0])}</h3><ul>{lis}</ul>'
        n = len(items)
        rows += (
            f'<details class="skill" id="{t}"><summary>{ico(t)}<span class="name">{e(name)}</span>'
            f'<span class="count">{n} project{"s" if n > 1 else ""}</span><span class="mix">{e(", ".join(mix))}</span></summary>'
            f'<div class="inside">{groups}<p class="more"><a href="/projects/#tool={t}">Show on the projects page</a></p></div></details>'
        )
    also = ""
    if rest:
        chips = "".join(f'<span class="tool" id="{t}">{ico(t)}{e(TOOLS[t])}</span>' for t in rest)
        also = f'<div class="also"><h2>Also in regular use</h2><div class="tools">{chips}</div></div>'
    body = f"""<main>
  <div class="pagehead"><div class="wrap">
    <h1>Skills</h1>
    <p class="sub">Select a tool to see the projects that use it.</p>
  </div></div>
  <div class="body"><div class="wrap">
    <div class="skills">{rows}</div>
    {also}
  </div></div>
</main>"""
    page("/skills/", f"Skills: {R['name']}", "Tools and the projects that use them.", "/skills/", body)


def contact():
    body = f"""<main>
  <div class="pagehead"><div class="wrap"><h1>Contact</h1></div></div>
  <div class="body"><div class="wrap">
    <ul class="contact">
      <li><span>Email</span><a href="mailto:{e(R['email'])}">{e(R['email'])}</a></li>
      <li><span>LinkedIn</span><a href="{e(R['linkedin'])}">linkedin.com/in/dzungdotran</a></li>
      <li><span>GitHub</span><a href="{e(R['github'])}">github.com/adriando-umich</a></li>
    </ul>
  </div></div>
</main>"""
    page("/contact/", f"Contact: {R['name']}", "Email, LinkedIn and GitHub.", "/contact/", body)


if __name__ == "__main__":
    home()
    projects_index()
    project_pages()
    resume()
    skills()
    contact()
    print("Built", 5 + len(PAGES), "pages")
