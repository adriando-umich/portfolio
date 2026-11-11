# Which customers to call in a bank telemarketing campaign.
# Six classifiers and a stacked model, each with a call cutoff chosen for profit.
# A sale earns $5 net; a call with no sale costs $1.
# Usage: Rscript analysis.R <calls.csv> [results.json]
suppressMessages({library(class); library(nnet); library(kernlab); library(rpart); library(randomForest)})

args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1], stringsAsFactors = TRUE)
d$X <- NULL
d$duration <- NULL          # known only after the call, so it cannot be used to choose whom to call
d$y <- factor(d$y, levels = c("no", "yes"))

# ---- Split: 50% train, 25% validation (two halves), 25% test, stratified --------
set.seed(12345)
part <- character(nrow(d))
for (cls in levels(d$y)) {
  i <- sample(which(d$y == cls)); n <- length(i)
  part[i] <- rep(c("train", "valA", "valB", "test"), times = c(floor(.5 * n), floor(.125 * n), floor(.125 * n), n - floor(.5 * n) - 2 * floor(.125 * n)))
}
tr <- d[part == "train", ]; rest <- d[part != "train", ]; rp <- part[part != "train"]

# Dummy variables scaled to 0-1 for kNN, the neural network and the SVM
M <- model.matrix(y ~ . - 1, d); lo <- apply(M[part == "train", ], 2, min); hi <- apply(M[part == "train", ], 2, max)
S <- sweep(sweep(M, 2, lo), 2, pmax(hi - lo, 1e-9), "/")
Str <- S[part == "train", ]; Sre <- S[part != "train", ]

# ---- First-level models: probability of a sale for every customer outside the training set ----
P <- data.frame(row.names = rownames(rest))
logit <- step(glm(y ~ ., tr, family = binomial), direction = "backward", trace = 0)
P$Logistic <- predict(logit, rest, type = "response")
k <- round(sqrt(nrow(tr))); k <- k + (k %% 2 == 0)
kn <- knn(Str, Sre, tr$y, k = k, prob = TRUE); pr <- attr(kn, "prob")
P$kNN <- ifelse(kn == "yes", pr, 1 - pr)
set.seed(12345); nn <- nnet(Str, class.ind(tr$y), size = 3, softmax = TRUE, maxit = 500, decay = 1e-3, trace = FALSE)
P$`Neural network` <- predict(nn, Sre)[, "yes"]
set.seed(12345); sv <- ksvm(Str, tr$y, type = "C-svc", kernel = "vanilladot", C = 1, prob.model = TRUE, scaled = FALSE)
P$SVM <- predict(sv, Sre, type = "probabilities")[, "yes"]
tree <- rpart(y ~ ., tr, method = "class", parms = list(split = "information"), control = rpart.control(cp = 0.001, maxdepth = 8))
P$`Decision tree` <- predict(tree, rest, type = "prob")[, "yes"]
set.seed(12345); rf <- randomForest(y ~ ., tr, ntree = 200, mtry = 14)
P$`Random forest` <- predict(rf, rest, type = "prob")[, "yes"]

# ---- Second level: a tree on the six probabilities, fitted on validation half A ----
A <- rp == "valA"; B <- rp == "valB"; TT <- rp == "test"
stack <- rpart(y ~ ., cbind(P[A, ], y = rest$y[A]), method = "class", control = rpart.control(cp = 0.002, maxdepth = 5, minbucket = 30))
P$Stacked <- predict(stack, P, type = "prob")[, "yes"]

# ---- Cutoffs: chosen for profit on validation half B, applied once to the test set ----
profit <- function(p, y, cut) { call <- p >= cut; 5 * sum(call & y == "yes") - sum(call & y == "no") }
grid <- seq(0.03, 0.60, by = 0.01)
yT <- rest$y[TT]; yB <- rest$y[B]
out <- do.call(rbind, lapply(names(P), function(m) {
  cut <- grid[which.max(sapply(grid, function(g) profit(P[B, m], yB, g)))]
  call <- P[TT, m] >= cut
  data.frame(model = m, cutoff = cut, calls = sum(call), sales = sum(call & yT == "yes"),
             call_rate = mean(call) * 100, hit_rate = mean(yT[call] == "yes") * 100, recall = sum(call & yT == "yes") / sum(yT == "yes") * 100,
             profit_default = profit(P[TT, m], yT, 0.5), profit = profit(P[TT, m], yT, cut))
}))
out <- out[order(-out$profit), ]
print(out, row.names = FALSE)

# Is the best model really better than the next ones? Bootstrap the test customers.
set.seed(12345); best <- out$model[1]
cuts <- setNames(out$cutoff, out$model); idx <- which(TT)
boot <- t(replicate(2000, { b <- sample(idx, replace = TRUE); sapply(names(P), function(m) profit(P[b, m], rest$y[b], cuts[m])) }))
wins <- sapply(setdiff(names(P), best), function(m) mean(boot[, best] > boot[, m]))
print(round(wins, 2))

res <- list(rows = nrow(d), success_rate = mean(d$y == "yes") * 100, test_rows = sum(TT), test_sales = sum(yT == "yes"),
            call_all = 5 * sum(yT == "yes") - sum(yT == "no"), models = out, best = best, best_beats = as.list(wins),
            logit_terms = attr(terms(logit), "term.labels"))
if (length(args) > 1) writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = 6, pretty = TRUE), args[2])
