"""Issue trees for the course project pages. Writes `tree` and `tree_h` into data/projects.json. Run from the repo root."""
import json
def N(t, s="", k="", q="", a="", ev="", c=()): return {"t": t, "s": s, "k": k, "q": q, "a": a, "ev": ev, "c": list(c)}
T = {
"fire-station-siting": ("The cost depends on which sites open; the 12-minute limit decides how few are enough",
  N("Total cost of the stations", "$700,000 in the answer", "root", c=[
    N("Stations opened", c=[
      N("Which sites open", "The lever: six yes/no choices", "lever", "Can two stations cover all six regions?", "Yes", "Sites 1 and 3 reach every region within 12 minutes."),
      N("Response-time limit", "The limit: 12 minutes to each region", "limit", "What does one minute less cost?", "$450,000", "An 11-minute limit needs three stations."),
      N("Siting rules", "The limit: three rules on which sites go together", "limit", "Do the rules change the answer?", "No", "The plan without the rules is the same.")]),
    N("Cost of each station", c=[N("Cost to open a site", "Fixed: $50,000 to $450,000 by site", "fixed"), N("Travel times", "Fixed: from each site to each region", "fixed")])])),
"supplier-bid-selection": ("The price of each bid is fixed, so the cost depends on which bids are accepted and on the rules they must meet",
  N("Total price of the accepted bids", "$4,470 in the answer", "root", c=[
    N("Bids accepted", c=[
      N("Which bids to accept", "The lever: 12 yes/no choices", "lever", "Is a mix of bids cheaper than one bundle from one supplier?", "Yes", "$4,470 against $4,639."),
      N("Price of each bid", "Fixed: set by the suppliers in the auction", "fixed")]),
    N("Rules that the plan must meet", c=[
      N("Each item is covered", "The limit: 12 items, each in one accepted bid or more", "limit"),
      N("Sourcing policies", "Local supplier, second source, strategic partners", "limit", "What does each policy add?", "$0 to $1,199", "Local supplier: $0. Second source: $999. Strategic partners: $1,199."),
      N("Minimum order of a supplier", "Supplier 1 wants $500 or more, or nothing", "limit", "Does the minimum change the plan?", "Yes", "The one-supplier bundle becomes the lowest cost, at $4,639.")])])),
"room-protection-pricing": ("Revenue comes from two rates; the cabins held back and the full rate are the two levers",
  N("Revenue per night", "$1,388 in the answer", "root", c=[
    N("Cabins sold at the low rate", c=[
      N("Cabins open at $100", "The lever: 10 less the cabins held back", "lever", "How many cabins to hold back?", "4", "Revenue is highest with 4, and within 1% with 5."),
      N("Leisure guests", "Fixed: 95% of guests, who pay $100 on average", "fixed")]),
    N("Cabins sold at the full rate", c=[
      N("Full rate", "The lever", "lever", "Which rate earns the most?", "$260", "Above $300, few business guests will pay."),
      N("Business guests", "Fixed: 5% of guests, who pay $300 on average", "fixed"),
      N("Held cabins that stay empty", "The limit: the cost of the wait", "limit", "How many stay empty?", "1.0 of 10", "On an average night, at the best policy.")])])),
"seasonal-production-plan": ("Four costs make the total; the plan trades inventory and overtime against changes in the workforce",
  N("Cost for the year", "$6.22M in the answer", "root", c=[
    N("Regular labor", c=[N("Workers each month", "The lever: 160 at the start, 237 at the peak", "lever"), N("Salary", "Fixed: $2,400 a month", "fixed")]),
    N("Changes in the workforce", c=[
      N("Hires and layoffs", "The lever. $1,800 for a hire, $1,200 for a layoff", "lever", "Is one workforce size all year cheaper?", "No", "A level workforce costs 8% more.")]),
    N("Overtime", c=[
      N("Workers on overtime", "The lever. $3,300 for a worker-month", "lever", "When does overtime pay?", "At the peak only", "Two months of the year."),
      N("Capacity", "The limit: one overtime shift for each worker; 13,000 units a month", "limit")]),
    N("Inventory", c=[
      N("Units held at month end", "The lever. $8 for a unit-month", "lever", "Is a plan with no inventory cheaper?", "No", "Production that follows demand costs 2% more.")])])),
"sealed-bid-decision": ("The bid moves two things in opposite directions: the chance to win and the profit of a win",
  N("Expected value of the bid", "$67k in the answer", "root", c=[
    N("Chance to win", c=[
      N("Bid amount", "The lever. A higher bid wins more often", "lever", "Which bid is best?", "$4.11M", "12% chance to win; 20% at $5M.")]),
    N("Expected result of a win", c=[
      N("Profit if the plan is approved", "$15M less $8M of capital, less the bid", "", "How high can the bid go?", "$5.68M", "Above this, the expected value is negative."),
      N("Chance of approval", "Fixed: 30%", "fixed", "How low can it go before a $5M bid loses money?", "20%", "The margin for error is 10 points."),
      N("Loss if the plan is not approved", "The limit: 10% of the bid", "limit")])])),
"telemarketing-call-list": ("Profit is sales less wasted calls; the model ranks the customers and the cutoff decides how many to call",
  N("Profit of the campaign", "$2,610 on the test customers", "root", c=[
    N("Sales: $5 each", c=[
      N("Model that ranks the customers", "The lever: seven models tested", "lever", "Does a complex model find more buyers?", "No", "A plain logistic regression is ahead of the six other models."),
      N("Customers who will buy", "Fixed: 11% of all customers", "fixed")]),
    N("Calls with no sale: $1 each", c=[
      N("Call cutoff", "The lever: the lowest probability that gets a call", "lever", "Which cutoff gives the most profit?", "17%", "The break-even probability: 1 sale in 6 calls."),
      N("Customers called", "16% of customers at this cutoff", "", "Do these calls find most of the buyers?", "Yes", "62% of all sales.")])])),
"product-line-pricing": ("Profit per customer is margin times the chance of a purchase, and the price moves the two in opposite directions",
  N("Expected profit per customer", "$1.08 today, $1.42 in the answer", "root", c=[
    N("Margin on each product", c=[
      N("Price", "The lever: 15 prices", "lever", "Which prices change?", "12 up, 3 down", "Eight go to the +20% limit."),
      N("Unit cost", "Fixed", "fixed")]),
    N("Chance that the customer buys the product", c=[
      N("Price sensitivity", "Estimated from 28,044 customer visits", "", "Does the sensitivity differ by product?", "Yes", "Lower for imported and straight-shape products."),
      N("Price range", "The limit: within 20% of the price today", "limit", "Does the limit decide the answer?", "Yes, for 8 products", "The model asks for more, outside the range of the data."),
      N("Share of customers who buy", "The limit: what the gain costs", "limit", "Does the share fall?", "Yes", "From 10.5% to 7.2%.")])])),
"marketplace-scale": ("A host's bookings depend on demand and on the chance that an inquiry is confirmed; listings act on the second part",
  N("Bookings of a host", "", "root", c=[
    N("Travelers who inquire", c=[N("Inquiries per day in the market", "Fixed: held constant in the model", "fixed")]),
    N("Chance that an inquiry is confirmed", c=[
      N("Listings in the market", "The lever of the growth team", "lever", "Do more listings cut the confirmation rate?", "Yes", "10% more listings: 1.7 points less, from an average of 21%."),
      N("Mix of listings", "Fixed: rooms, apartments, executive listings, location", "fixed")]),
    N("Nights occupied", c=[
      N("Occupancy rate", "", "", "Does occupancy fall too?", "Not clear", "0.25 points less, but p = 0.13.")])])),
"lending-growth-and-losses": ("Losses are volume times the charge-off rate; the grade is the split that separates risk best",
  N("Credit losses of the platform", "", "root", c=[
    N("Loan volume", c=[
      N("Number of loans", "603 in 2007, 134,814 in 2013", "", "How fast did the platform grow?", "224 times", "With a stop of some months in 2008."),
      N("Average loan", "$8,255 to $14,707", "")]),
    N("Charge-off rate", "15.5% of completed loans", "", c=[
      N("By grade", "The lever for an investor: which grades to buy", "lever", "Does the grade separate risk?", "Yes", "6% for grade A, 37% for grade G."),
      N("By year of issue", "", "", "Did risk rise with growth?", "In part", "12.6% for 2009 loans, 16.2% for 2012 loans."),
      N("By state", "", "", "Do states differ?", "Yes", "8.9% to 19.3% among states with 500 loans or more.")])])),
"classroom-crowdfunding": ("Some drivers of funding are in the hands of the teacher; the price of the request is the strongest",
  N("Chance that a project is funded", "70% of closed projects", "root", c=[
    N("What the teacher controls", c=[
      N("Price of the request", "The lever", "lever", "Does a lower price help?", "Yes", "90% funded below $200, 45% above $1,500."),
      N("Type of resource", "The lever", "lever", "Does the resource matter?", "Yes", "Books 77%, technology 63%.")]),
    N("What the teacher does not control", c=[
      N("Poverty level of the school", "Fixed", "fixed", "Are the poorest schools funded less?", "No", "73% for the highest poverty level, 67% to 68% for the others."),
      N("Year", "Fixed", "fixed", "Did the rate fall as the site grew?", "No", "Near 70% from 2010 to 2016.")])])),
}
d = json.load(open("data/projects.json", encoding="utf-8"))
for p in d["projects"]:
    if p.get("slug") in T: p["tree_h"], p["tree"] = T[p["slug"]]
json.dump(d, open("data/projects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sum(1 for p in d["projects"] if p["type"] == "course" and p.get("tree")), "of", sum(1 for p in d["projects"] if p["type"] == "course"))
