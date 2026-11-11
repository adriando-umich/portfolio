"""Write the page fragments for the R course projects from analysis/<slug>/results.json. Run from the repo root."""
import json, math, shutil, os

def load(slug): return json.load(open(f"analysis/{slug}/results.json"))
def out(slug, html):
    open(f"data/course/{slug}.html", "w", encoding="utf-8").write(html)
    os.makedirs(f"projects/{slug}", exist_ok=True); shutil.copy(f"analysis/{slug}/analysis.R", f"projects/{slug}/analysis.R")
def kpis(items):
    return '<div class="cp-kpis">' + "".join(f'<div><p class="k">{k}</p><p class="v">{v}</p><p class="s">{s}</p></div>' for k, v, s in items) + "</div>"
def model(cols):
    return '<div class="cp-model">' + "".join(f"<div><h3>{h}</h3><p>{t}</p></div>" for h, t in cols) + "</div>"
def notes(items): return '<ul class="notes">' + "".join(f"<li>{t}</li>" for t in items) + "</ul>"
def bar(label, width, value, side, on=False, wide=False, neg=False):
    return (f'<div class="cp-bar{" wide" if wide else ""}{" on" if on else ""}{" neg" if neg else ""}"><span class="c">{label}</span><span class="t"><i style="width:{max(width, 0.5):.1f}%"></i></span>'
            f'<span class="v">{value}</span><span class="s">{side}</span></div>')
def money(x): return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"

# ------------------------------------------------------------------ marketplace scale
def marketplace():
    r = load("marketplace-scale"); k = math.log(1.1) * 100
    c, o = r["confirmation"], r["occupancy"]
    rows = ""
    for name, x, unit in (("Booking confirmation rate", c, c["mean"] * 100), ("Occupancy rate", o, o["mean"] * 100)):
        for lab, m in (("Plain regression", x["ols"]), ("With the instrument", x["iv"])):
            pts = m["coef"] * k
            sig = "clear at the 5% level" if m["p"] < 0.05 else "not statistically clear"
            rows += (f'<tr><td>{name}<span class="sub">average {unit:.1f}%</span></td><td>{lab}</td><td class="n{" strong" if lab != "Plain regression" and m["p"] < .05 else ""}">{pts:+.2f} points</td>'
                     f'<td class="n">{m["p"]:.2f}</td><td>{sig}</td></tr>')
    html = kpis([
        ("Booking confirmation rate, for 10% more listings", f'{c["iv"]["coef"] * k:+.1f} pts', f'from an average of {c["mean"] * 100:.0f}%; clear at the 5% level'),
        ("The same effect in a plain regression", f'{c["ols"]["coef"] * k:+.1f} pts', "the competition effect is hidden, because good markets attract listings"),
        ("Strength of the instrument", f'F = {r["first_stage"]["f"]:.1f}', "above the usual minimum of 10, but not by much"),
    ]) + f"""
<section class="part"><h2>A plain regression shows no effect; the instrument shows that more listings cut confirmations</h2>
  <div class="table-scroll"><table class="cp-table">
    <caption>Effect of 10% more listings in a market, {r["n"]} local markets</caption>
    <thead><tr><th scope="col">Outcome for hosts</th><th scope="col">Method</th><th scope="col" class="n">Effect</th><th scope="col" class="n">p-value</th><th scope="col">Reading</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="cp-note">Standard errors are robust to heteroskedasticity. Controls: inquiries per day, average number of rooms, share of apartments, share of executive listings, share near adventure sites and national parks.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Question", "Does a larger market bring each host more bookings (more travelers come) or fewer (more hosts compete)?"),
          ("Problem", "Listings are not random. Hosts enter the markets where demand is already good, so a plain regression mixes the two directions."),
          ("Method", "Two-stage least squares. New listings from a migration of hosts move the market size for a reason that is not local demand.")])}
  {notes([f'The occupancy effect has the same sign ({o["iv"]["coef"] * k:+.2f} points) but is not statistically clear (p = {o["iv"]["p"]:.2f}).',
          f'The first-stage F statistic is {r["first_stage"]["f"]:.1f}. The instrument is usable, but the estimates are not precise.',
          "For the marketplace, the result points to demand: more travelers, not more hosts, are what the weak markets need.",
          "The instrument is valid only if the new listings affect confirmations through market size alone. The data cannot test this."])}
</section>"""
    out("marketplace-scale", html)

# ------------------------------------------------------------------ product line pricing
def pricing():
    r = load("product-line-pricing"); P = r["products"]
    gain = (r["profit_new"] / r["profit_now"] - 1) * 100
    up = [p for p in P if p["change_pct"] > 0]; down = [p for p in P if p["change_pct"] < 0]; cap = [p for p in P if abs(p["change_pct"]) > 19.99]
    rows = ""
    for p in P:
        w = abs(p["change_pct"]) / 20 * 100
        neg = p["change_pct"] < 0
        rows += (f'<tr><td>Product {p["product"]}</td><td class="n">${p["cost"]:.2f}</td><td class="n">${p["price_now"]:.2f}</td><td class="n strong">${p["price_new"]:.2f}</td>'
                 f'<td class="chg"><span class="{"dn" if neg else "up"}"><i style="width:{w / 2:.1f}%"></i></span></td><td class="n{" neg" if neg else ""}">{p["change_pct"]:+.0f}%{"*" if abs(p["change_pct"]) > 19.99 else ""}</td>'
                 f'<td class="n">{(p["price_now"] - p["cost"]) / p["price_now"] * 100:.0f}%</td><td class="n">{(p["price_new"] - p["cost"]) / p["price_new"] * 100:.0f}%</td></tr>')
    co, se = r["coef"], r["se"]
    names = {"price": "Base effect of $1 more", "price:imported": "Imported", "price:straightshape": "Straight shape", "price:slowflow": "Slow flow", "price:below6month": "Age below 6 months", "price:sizesmall": "Small size", "price:wideneck": "Wide neck"}
    top = max(abs(v) for v in co.values()); feats = ""
    for kname in ["price"] + sorted([x for x in co if x != "price"], key=lambda x: -co[x]):
        v = co[kname]; clear = abs(v / se[kname]) > 1.96
        feats += bar(names[kname], abs(v) / top * 100, f"{v:+.3f}", ("clear" if clear else "not clear") + (", less sensitive to price" if v > 0 and clear else ""), on=kname == "price", neg=v < 0)
    html = kpis([
        ("Expected profit per customer", f"+{gain:.0f}%", f'${r["profit_now"]:.2f} to ${r["profit_new"]:.2f}, with each price inside a ±20% limit'),
        ("Price changes", f"{len(up)} up, {len(down)} down", f"{len(cap)} products stop at the +20% limit"),
        ("Share of customers who buy", f'{r["buy_now"] * 100:.1f}% to {r["buy_new"] * 100:.1f}%', "fewer sales at a higher margin: the cost of the gain"),
    ]) + f"""
<section class="part"><h2>Twelve prices go up, eight of them to the limit, and three high-margin prices come down</h2>
  <div class="table-scroll"><table class="cp-table prices">
    <thead><tr><th scope="col">Product</th><th scope="col" class="n">Unit cost</th><th scope="col" class="n">Price now</th><th scope="col" class="n">New price</th><th scope="col" colspan="2">Change</th><th scope="col" class="n">Margin now</th><th scope="col" class="n">New margin</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="cp-note">* The price stops at the +20% limit. Without the limit, the model asks for a larger increase, outside the range of prices in the data.</p>
</section>
<section class="part"><h2>Customers are less sensitive to the price of imported and straight-shape products</h2>
  <div class="cp-bars feats" role="img" aria-label="Estimated effect of price on utility, and how each product feature changes it.">{feats}</div>
  <p class="cp-note">Multinomial logit on {r["customers"]:,} customer visits; {r["buy_rate"] * 100:.0f}% end with a purchase. A positive value makes the price effect weaker for products with that feature. "Clear" means clear at the 5% level.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Demand", "Each customer chooses one of 15 products or no purchase. The price effect is different for each product, through six product features."),
          ("Decision", "The 15 prices, each within 20% of the current average price."),
          ("Objective", "The highest expected profit per customer: margin times the probability of a purchase, summed over the products.")])}
  {notes([f"Eight products go to the +20% limit, so the limit decides most of the answer. A test in the market must come before larger increases.",
          f'The gain has a cost: the share of customers who buy falls from {r["buy_now"] * 100:.1f}% to {r["buy_new"] * 100:.1f}%. If customer count has value beyond this purchase, the increase must be smaller.',
          "Products 7, 8 and 14 have high margins and price-sensitive customers. A lower price brings more than enough volume.",
          "The demand model has no competitor prices. The result assumes that competitors do not react."])}
</section>"""
    out("product-line-pricing", html)

# ------------------------------------------------------------------ telemarketing
def tele():
    r = load("telemarketing-call-list"); M = r["models"]; best = M[0]; top = max(m["profit"] for m in M)
    rows = ""
    for m in M:
        rows += (f'<div class="cp-bar wide{" on" if m is best else ""}"><span class="c"><b>{m["model"]}</b>call if the probability is {m["cutoff"] * 100:.0f}% or more</span>'
                 f'<span class="t"><i style="width:{m["profit"] / top * 100:.1f}%"></i></span><span class="v">{money(m["profit"])}</span>'
                 f'<span class="s">{money(m["profit_default"])} at the 50% cutoff<br>calls {m["call_rate"]:.0f}% of customers</span></div>')
    n = r["test_rows"]; six = M[:6]
    add, spread = best["profit"] - best["profit_default"], six[0]["profit"] - six[-1]["profit"]
    html = kpis([
        ("Profit from the test customers", money(best["profit"]), f'{n:,} customers; {money(best["profit_default"])} with the usual 50% cutoff'),
        ("Customers to call", f'{best["call_rate"]:.0f}%', f'they give {best["recall"]:.0f}% of all sales; {best["hit_rate"]:.0f}% of the calls end in a sale'),
        ("Profit if the bank calls everyone", money(r["call_all"]), f'only {r["success_rate"]:.1f}% of calls end in a sale'),
    ]) + f"""
<section class="part"><h2>The cutoff matters more than the model: it adds {money(add)} to the best model, and the top six models are within {money(spread)} of each other</h2>
  <div class="cp-bars" role="img" aria-label="Profit on the test customers for each model, with a cutoff chosen for profit and with the 50% cutoff.">{rows}</div>
  <p class="cp-note">A sale earns $5 net and a call with no sale costs $1, so a call pays when the probability of a sale is above 1 in 6 (17%). Each cutoff was chosen on validation data and applied once to the test customers.</p>
</section>
<section class="part"><h2>The model</h2>
  {model([("Decision", "Call or do not call each customer, from data that the bank has before the call."),
          ("Objective", "The highest profit: $5 for each sale, less $1 for each call with no sale."),
          ("Method", "Six classifiers and a stacked model. Data split: 50% to train, 25% to choose the cutoffs and fit the stacked model, 25% to test.")])}
  {notes([f'The plain logistic regression has the highest profit. In 2,000 resamples of the test customers, it is ahead of each other model more than 99% of the time.',
          "The stacked model does not add profit here. The six models make similar errors, so there is little for a second level to correct.",
          f'The cutoff of the logistic regression ({best["cutoff"] * 100:.0f}%) is the same as the break-even probability. Its probabilities are well calibrated; those of the SVM are not.',
          "Call duration is not a model input. It is known only after the call."])}
</section>"""
    out("telemarketing-call-list", html)

if __name__ == "__main__":
    marketplace(); pricing(); tele(); print("ok")
