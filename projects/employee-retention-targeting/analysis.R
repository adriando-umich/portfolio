# Which employees to approach with a retention offer.
# Logistic regression and a random forest, scored by the money a retention program saves.
# Usage: Rscript analysis.R <hr.csv> [results.json]
suppressMessages(library(randomForest))
args <- commandArgs(trailingOnly = TRUE)
raw <- read.csv(args[1], stringsAsFactors = TRUE)
raw[[1]] <- NULL                                           # row number
names(raw) <- c("satisfaction", "evaluation", "projects", "hours", "tenure", "accident", "left", "promoted", "department", "salary")

# The file has many repeated profiles. If the same profile is in the training and the test data,
# the test result is too good. Keep one row for each profile.
d <- unique(raw)
dup <- list(rows = nrow(raw), unique = nrow(d), left_raw = mean(raw$left), left_unique = mean(d$left))

set.seed(12345)
i <- sample(nrow(d), floor(0.7 * nrow(d))); tr <- d[i, ]; te <- d[-i, ]

base  <- glm(left ~ ., tr, family = binomial)
upper <- left ~ . + I(satisfaction^2) + I(evaluation^2) + I(projects^2) + I(hours^2) + I(tenure^2) +
  satisfaction:evaluation + satisfaction:projects + satisfaction:hours + satisfaction:tenure + evaluation:projects + evaluation:hours + projects:hours + projects:tenure
curve <- step(base, scope = list(lower = left ~ 1, upper = upper), direction = "both", trace = 0)
set.seed(12345); rf <- randomForest(factor(left) ~ ., tr, ntree = 300, importance = TRUE)
P <- list(`Logistic regression, main effects` = predict(base, te, type = "response"),
          `Logistic regression with curves and interactions` = predict(curve, te, type = "response"),
          `Random forest` = predict(rf, te, type = "prob")[, "1"])

# Business case (assumptions): to replace an employee costs $25,000; a retention offer costs $10,000
# and keeps 60% of the employees who would leave. An offer pays when p * 0.6 * 25,000 > 10,000.
REPLACE <- 25000; OFFER <- 10000; KEEP <- 0.60; cut <- OFFER / (KEEP * REPLACE)
auc <- function(p, y) { r <- rank(p); n1 <- sum(y == 1); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * sum(y == 0)) }
score <- function(p, y) {
  flag <- p >= cut; tp <- sum(flag & y == 1); fp <- sum(flag & y == 0)
  data.frame(auc = auc(p, y), flagged = sum(flag), leavers_found = tp, false_alarms = fp, recall = tp / sum(y == 1) * 100,
             precision = tp / max(sum(flag), 1) * 100, saving = tp * KEEP * REPLACE - sum(flag) * OFFER)
}
out <- do.call(rbind, lapply(names(P), function(m) cbind(model = m, score(P[[m]], te$left))))
print(out, row.names = FALSE)

# How much do the repeated profiles inflate the result? Same random forest, split made on all rows.
set.seed(12345); j <- sample(nrow(raw), floor(0.7 * nrow(raw)))
rf_raw <- randomForest(factor(left) ~ ., raw[j, ], ntree = 300)
acc <- function(p, y) mean((p >= 0.5) == (y == 1))
inflate <- list(accuracy_with_repeats = acc(predict(rf_raw, raw[-j, ], type = "prob")[, "1"], raw$left[-j]), accuracy_unique = acc(P[["Random forest"]], te$left),
                logit_with_repeats = acc(predict(glm(left ~ ., raw[j, ], family = binomial), raw[-j, ], type = "response"), raw$left[-j]), logit_unique = acc(P[[1]], te$left))

imp <- sort(importance(rf)[, "MeanDecreaseGini"], decreasing = TRUE)
# Who leaves: three groups that the forest separates (rates on all unique profiles)
grp <- with(d, ifelse(projects <= 2 & satisfaction < 0.5 & evaluation < 0.6, "Low load, low rating", ifelse(projects >= 6 | hours >= 270, "Overloaded",
            ifelse(tenure >= 5 & tenure <= 6 & evaluation >= 0.8 & satisfaction >= 0.7, "Strong performers at 5 to 6 years", "All other employees"))))
groups <- aggregate(left ~ grp, data.frame(grp, left = d$left), function(v) c(n = length(v), rate = mean(v) * 100))
groups <- data.frame(group = groups$grp, n = groups$left[, "n"], rate = groups$left[, "rate"])
print(groups); print(unlist(inflate)); print(round(imp, 0))
res <- list(dup = dup, test_rows = nrow(te), test_leavers = sum(te$left), cutoff = cut, replace = REPLACE, offer = OFFER, keep = KEEP,
            offer_all = sum(te$left) * KEEP * REPLACE - nrow(te) * OFFER, models = out, inflate = inflate,
            importance = as.list(round(imp / sum(imp) * 100, 1)), groups = groups, curve_terms = attr(terms(curve), "term.labels"))
if (length(args) > 1) writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = 6, pretty = TRUE), args[2])
