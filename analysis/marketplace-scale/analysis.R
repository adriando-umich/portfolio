# Does a larger local market help or hurt hosts on a vacation rental marketplace?
# Two-stage least squares. Unit of analysis: one local market.
# Usage: Rscript analysis.R <markets.csv> [results.json]
library(AER)        # ivreg
library(sandwich)   # heteroskedasticity-robust standard errors
library(lmtest)

args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1])

# Listings, inquiries and new listings are right-skewed, so they enter in logs.
d$ln_listings     <- log(d$num_listing + 1)
d$ln_inquiries    <- log(d$num_inquiry_per_day + 1)
d$ln_new_listings <- log(d$num_new_listing + 1)   # instrument

controls <- "ln_inquiries + avg_num_rooms + percent_apt + percent_executive + percent_close_adventure + percent_close_natlpark"
robust <- function(m) coeftest(m, vcov = vcovHC(m, type = "HC1"))

estimate <- function(outcome) {
  ols <- lm(as.formula(paste(outcome, "~ ln_listings +", controls)), data = d)
  iv  <- ivreg(as.formula(paste(outcome, "~ ln_listings +", controls, "| ln_new_listings +", controls)), data = d)
  o <- robust(ols)["ln_listings", ]; i <- robust(iv)["ln_listings", ]
  list(mean = mean(d[[outcome]]),
       ols = list(coef = o[[1]], se = o[[2]], p = o[[4]]),
       iv  = list(coef = i[[1]], se = i[[2]], p = i[[4]]))
}

# First stage: does the instrument move the number of listings?
first <- lm(as.formula(paste("ln_listings ~ ln_new_listings +", controls)), data = d)
f_classic <- summary(first)$coefficients["ln_new_listings", "t value"]^2
f_robust  <- robust(first)["ln_new_listings", "t value"]^2

res <- list(n = nrow(d),
            median_listings = median(d$num_listing),
            first_stage = list(coef = coef(first)[["ln_new_listings"]], f = f_classic, f_robust = f_robust),
            occupancy = estimate("occupancy_rate"),
            confirmation = estimate("confirmation_rate"))
print(str(res))
if (length(args) > 1) writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = 8, pretty = TRUE), args[2])
