# How many rooms a hotel can overbook when it knows the cancellation risk of each booking.
# Models are fitted on arrivals in 2015 and 2016 and tested on arrivals in 2017 (out of time).
# Usage: Rscript analysis.R <bookings.csv> [results.json]
suppressMessages({library(rpart); library(randomForest)})
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1], stringsAsFactors = FALSE)

# Keep only what the hotel knows when the booking is made. The reservation status, the assigned room,
# later booking changes and the days on the waiting list are known later, so they are not model inputs.
d$children[is.na(d$children)] <- 0
d$has_agent <- as.integer(d$agent != "NULL"); d$has_company <- as.integer(d$company != "NULL")
top <- names(sort(table(d$country[d$arrival_date_year < 2017]), decreasing = TRUE))[1:12]
d$country <- ifelse(d$country %in% top, d$country, "Other")
d$nights <- d$stays_in_weekend_nights + d$stays_in_week_nights
d$date <- as.Date(paste(d$arrival_date_year, d$arrival_date_month, d$arrival_date_day_of_month), format = "%Y %B %d")
keep <- c("is_canceled", "hotel", "lead_time", "arrival_date_month", "stays_in_weekend_nights", "stays_in_week_nights", "adults", "children", "babies", "meal", "country",
          "market_segment", "distribution_channel", "is_repeated_guest", "previous_cancellations", "previous_bookings_not_canceled", "reserved_room_type",
          "deposit_type", "has_agent", "has_company", "customer_type", "adr", "required_car_parking_spaces", "total_of_special_requests")
m <- d[, keep]; for (v in names(m)) if (is.character(m[[v]])) m[[v]] <- factor(m[[v]])
train <- d$arrival_date_year < 2017; tr <- m[train, ]; te <- m[!train, ]
for (v in names(te)) if (is.factor(te[[v]])) { bad <- !(te[[v]] %in% unique(tr[[v]])); if (any(bad)) te[[v]][bad] <- names(sort(table(tr[[v]]), decreasing = TRUE))[1] }

logit <- suppressWarnings(glm(is_canceled ~ ., tr, family = binomial))
tree  <- rpart(factor(is_canceled) ~ ., tr, method = "class", control = rpart.control(cp = 0.001, maxdepth = 8))
set.seed(12345); rf <- randomForest(factor(is_canceled) ~ ., tr, ntree = 150, sampsize = 30000, importance = TRUE)
P <- data.frame(`Logistic regression` = suppressWarnings(predict(logit, te, type = "response")), `Decision tree` = predict(tree, te, type = "prob")[, "1"],
                `Random forest` = predict(rf, te, type = "prob")[, "1"], check.names = FALSE)
P$`Flat rate by hotel` <- ave(tr$is_canceled, tr$hotel)[match(te$hotel, tr$hotel)]      # the usual rule: one historical rate
y <- te$is_canceled
auc <- function(p, y) { r <- rank(p); n1 <- sum(y == 1); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * sum(y == 0)) }

# Use of the model: for each hotel and arrival day, expected cancellations = sum of the probabilities.
# Overbook by the expected cancellations less a safety margin of one standard deviation.
day <- interaction(d$hotel[!train], d$date[!train], drop = TRUE)
by_day <- function(p) {
  exp <- tapply(p, day, sum); sd <- sqrt(tapply(p * (1 - p), day, sum)); act <- tapply(y, day, sum); n <- tapply(y, day, length)
  over <- pmax(floor(exp - sd), 0)
  c(mae = mean(abs(exp - act)), bias = sum(exp) / sum(act) - 1, overbooked = sum(over), recovered = sum(pmin(over, act)), walked = sum(pmax(over - act, 0)),
    days = length(act), days_walked = sum(over > act), cancels = sum(act), bookings = sum(n))
}
out <- do.call(rbind, lapply(names(P), function(k) data.frame(model = k, auc = auc(P[[k]], y), accuracy = mean((P[[k]] >= 0.5) == (y == 1)) * 100, t(by_day(P[[k]])))))
print(out, row.names = FALSE)

imp <- sort(importance(rf)[, "MeanDecreaseGini"], decreasing = TRUE)
rate <- function(f) round(tapply(d$is_canceled, f, mean) * 100, 1)
lead <- cut(d$lead_time, c(-1, 7, 30, 90, 180, 800), labels = c("0 to 7 days", "8 to 30 days", "31 to 90 days", "91 to 180 days", "More than 180 days"))
res <- list(rows = nrow(d), train_rows = sum(train), test_rows = sum(!train), cancel_rate = mean(d$is_canceled) * 100, test_cancel_rate = mean(y) * 100, train_cancel_rate = mean(tr$is_canceled) * 100,
            models = out, importance = as.list(round(imp / sum(imp) * 100, 1)), by_lead = as.list(rate(lead)), by_deposit = as.list(rate(d$deposit_type)),
            by_requests = as.list(rate(pmin(d$total_of_special_requests, 3))), by_segment = as.list(rate(d$market_segment)), lead_n = as.list(table(lead)))
print(res$by_lead); print(res$by_deposit); print(round(imp / sum(imp) * 100, 1)[1:8])
if (length(args) > 1) writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = 6, pretty = TRUE), args[2])
