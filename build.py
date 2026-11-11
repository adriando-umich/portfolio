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


def home():
    proofs = "".join(
        f'<li><a href="{url(p)}"><span class="name">{e(p["short"])}</span><span class="num">{e(p["num"])}</span>'
        f'<span class="what">{e(p["what"])}</span><span class="go">Open the {e(p["short"].lower())}</span></a></li>'
        for p in CASES
    )
    strip = "".join(f'<a href="/skills/#{t}">{ico(t)}{e(n)}</a>' for t, n in TOOLS.items())
    jobs = "".join(
        f'<li><span class="when">{e(j["period"])}</span><span class="org">{e(j["org"])}</span>'
        f'<span class="did">{e(", ".join(r["title"] for r in j["roles"]))}</span></li>'
        for j in R["experience"]
    )
    body = f"""<header class="lead">
  <div class="wrap">
    <p class="role">{e(R['role'])}</p>
    <h1>{e(R['claim'])}</h1>
    <p class="background">{e(R['background'])}</p>
    <p class="actions"><a class="btn solid" href="/projects/">See all projects</a><a class="btn" href="/resume/">Read the resume</a></p>
    <ul class="proofs">{proofs}</ul>
  </div>
</header>
<main>
  <section class="section">
    <div class="wrap">
      <h2>Ten years of work across audit, finance and strategy</h2>
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
    page("/", f"{R['name']}: strategy and analytics", R["claim"], "/", body)


def project_row(p):
    head = f'<a href="{url(p)}">{e(p["title"])}</a>' if p.get("slug") else e(p["title"])
    meta = f'<b>{e(p["org"])}</b>{e(p.get("period", ""))}' if p.get("org") else "<b>Practice set</b>"
    return (
        f'<li class="prow" data-tools="{" ".join(p["tools"])}"><div class="meta">{meta}</div>'
        f'<div><h3>{head}</h3><p>{e(p["result"])}</p></div>{tools(p["tools"]) or "<div></div>"}</li>'
    )


def projects_index():
    used = [t for t in TOOLS if any(t in p["tools"] for p in PROJECTS)]
    buttons = '<button type="button" data-tool="" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" data-tool="{t}" aria-pressed="false">{ico(t)}{e(TOOLS[t])}</button>' for t in used
    )
    groups = ""
    for t in P["types"]:
        items = [p for p in PROJECTS if p["type"] == t["id"]]
        if not items:
            continue
        if t["id"] == "case":
            inner = '<div class="cards">' + "".join(
                f'<a class="card" href="{url(p)}" data-tools="{" ".join(p["tools"])}"><span class="name">{e(p["title"])}</span>'
                f'<span class="num">{e(p["num"])}</span><span class="what">{e(p["what"])}</span>'
                f'<span class="q">Q: {e(p["question"])}</span>{tools(p["tools"])}<span class="go">Open the case</span></a>'
                for p in items
            ) + "</div>"
        else:
            inner = '<ul class="rows">' + "".join(project_row(p) for p in items) + "</ul>"
        note = f'<p class="note">{e(t["note"])}</p>' if t["note"] else ""
        groups += f'<section class="group" id="{t["id"]}"><h2>{e(t["name"])}</h2>{note}{inner}</section>'
    n_work = len([p for p in PROJECTS if p["type"] == "work"])
    body = f"""<main>
  <div class="pagehead"><div class="wrap">
    <h1>Projects</h1>
    <p class="sub">{len(CASES)} case studies with a recommendation and its dollar effect, {n_work} results from work, and practice sets in SQL and Python.</p>
  </div></div>
  <div class="body"><div class="wrap">
    <div class="filter" role="group" aria-label="Filter projects by tool"><span class="label">Filter by tool</span>{buttons}</div>
    {groups}
    <p class="empty">No project uses this tool yet.</p>
  </div></div>
</main>"""
    page("/projects/", f"Projects: {R['name']}", "Case studies, results from work and practice sets.", "/projects/", body)


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
            key = "".join(f'<li><h3>{e(k["h"])}</h3><p>{k["p"]}</p></li>' for k in p["keyline"])
            body = f"""<main>
  <div class="pagehead"><div class="wrap">{crumb}
    <h1>{e(p['title'])}</h1>
  </div></div>
  <div class="body"><div class="wrap">
    <div class="case-head"><p class="facts">{e(p['data'])}</p>{tools(p['tools'])}</div>
    <p class="question">Q: {e(p['question'])}</p>
    <h2 class="answer">{e(p['answer'])}</h2>
    <p class="why">{e(p['why'])}</p>
    <ol class="keyline">{key}</ol>
    {CHART if p.get('exhibit') == 'credit' else ''}
    {pager(p)}
  </div></div>
</main>"""
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
    <h2>Tools</h2><div style="margin-top:20px">{tools(list(TOOLS))}</div>
  </div></div>
</main>"""
    page("/resume/", f"Resume: {R['name']}", R["background"], "/resume/", body)


def skills():
    cards, rest = "", []
    for t, name in TOOLS.items():
        items = [p for p in PROJECTS if t in p["tools"]]
        if not items:
            rest.append(t)
            continue
        lis = ""
        for p in items:
            label = f'<a href="{url(p)}">{e(p["title"])}</a>' if p.get("slug") else e(p["title"])
            where = f' <span>({e(p["org"])})</span>' if p.get("org") else ""
            lis += f"<li>{label}{where}</li>"
        n = len(items)
        cards += (
            f'<section class="skill" id="{t}"><div class="top">{ico(t)}<h2>{e(name)}</h2></div>'
            f'<p class="count">{n} project{"s" if n > 1 else ""}</p><ul>{lis}</ul>'
            f'<p class="count"><a href="/projects/#tool={t}">Show on the projects page</a></p></section>'
        )
    also = ""
    if rest:
        chips = "".join(f'<span class="tool" id="{t}">{ico(t)}{e(TOOLS[t])}</span>' for t in rest)
        also = f'<div class="also"><h2>Also in regular use</h2><div class="tools">{chips}</div></div>'
    body = f"""<main>
  <div class="pagehead"><div class="wrap">
    <h1>Skills</h1>
    <p class="sub">Each tool links to the projects that use it.</p>
  </div></div>
  <div class="body"><div class="wrap">
    <div class="skills">{cards}</div>
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
