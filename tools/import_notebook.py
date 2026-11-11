"""Import one Quarto notebook (notebook.html) into the site.

Usage:  python3 tools/import_notebook.py <slug> <path to notebook.html> <rollout heading prefix>
Example: python3 tools/import_notebook.py credit-approval-cutoff ".../01-credit-lifecycle/notebook.html" 7e.

The script writes:
  projects/<slug>/notebook/index.html   the full notebook, unchanged except the employer name in the disclaimer
  data/briefs/<slug>.html               the short technical brief (selected sections, no code)
  data/briefs/<slug>.json               the evaluation table and the recommendation list
Run build.py after this script.
"""
import json
import os
import re
import sys

from bs4 import BeautifulSoup

slug, src, rollout = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(src, encoding="utf-8").read()

# 1. Full notebook. The site is not for one employer, so the disclaimer names no company.
full = raw.replace("The data is not Capital One data.", "The data is not the data of an employer or a client.")
full = re.sub(r"(This data is not|The data is not) (the )?data of Capital One\.", "The data is not the data of an employer or a client.", full)
os.makedirs(f"projects/{slug}/notebook", exist_ok=True)
open(f"projects/{slug}/notebook/index.html", "w", encoding="utf-8").write(full)

soup = BeautifulSoup(raw, "lxml")
sections = {}
for sec in soup.select("section.level2"):
    h = sec.find("h2")
    if h:
        sections[h.get_text(" ", strip=True)] = sec


def find(prefix):
    for name, sec in sections.items():
        if name.startswith(prefix):
            return name, sec
    raise SystemExit(f"Section not found: {prefix}")


def clean(sec):
    """Return the section as HTML with no code, no technical notes and links that go to the full notebook."""
    sec = BeautifulSoup(str(sec), "lxml").find("section")
    for x in sec.select("details, pre, script, style, .cell-code, .tech-note, h2, .anchorjs-link, a.anchorjs-link"):
        x.decompose()
    for a in sec.find_all("a", href=True):
        if a["href"].startswith("#"):
            a["href"] = "notebook/" + a["href"]
    for t in sec.find_all("table"):
        t.attrs = {}
        wrap = soup.new_tag("div", attrs={"class": "table-scroll"})
        t.wrap(wrap)
    for tag in sec.find_all(True):
        keep = {}
        if tag.name == "a":
            keep = {"href": tag.get("href")}
        elif tag.name == "img":
            keep = {"src": tag.get("src"), "alt": tag.get("alt") or "Chart from the notebook"}
        elif tag.name == "div":
            cls = [c for c in (tag.get("class") or []) if c in ("business-note", "decision", "table-scroll")]
            if cls:
                keep = {"class": cls}
        elif tag.name in ("td", "th"):
            keep = {k: tag.get(k) for k in ("colspan", "rowspan") if tag.get(k)}
        tag.attrs = keep
    html = sec.decode_contents()
    return re.sub(r"\n\s*\n+", "\n", html).strip()


def title(name):
    return re.sub(r"^\d[a-z]\.\s*", "", name)


parts = []
for prefix in ("2e.", "6d.", rollout, "What a reviewer should challenge", "Next steps"):
    name, sec = find(prefix)
    parts.append(f'<section class="bpart"><h3>{title(name)}</h3>\n{clean(sec)}\n</section>')
os.makedirs("data/briefs", exist_ok=True)
open(f"data/briefs/{slug}.html", "w", encoding="utf-8").write("\n".join(parts))

# 2. Evaluation table (section 6f) and recommendation list.
_, ev = find("6f.")
rows = []
for tr in ev.select("table tr"):
    cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
    if len(cells) >= 5 and re.match(r"^\d\.", cells[0]):
        rows.append(cells[:5])
_, rec = find("Recommendation")
recs = []
for li in BeautifulSoup(clean(rec), "lxml").find_all("li"):
    recs.append(li.decode_contents().strip())
_, ans = find("The answer")
answer = [p.get_text(" ", strip=True) for p in ans.find_all("p")]
json.dump({"evaluation": rows, "recommendations": recs, "answer": answer},
          open(f"data/briefs/{slug}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(slug, "brief words:", len(BeautifulSoup("".join(parts), "lxml").get_text(" ").split()), "evaluation rows:", len(rows), "recommendations:", len(recs))
