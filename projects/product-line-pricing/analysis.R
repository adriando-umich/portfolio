# How to reprice a 15-product line when price sensitivity differs by product feature.
# Step 1: multinomial logit demand model (maximum likelihood, base R).
# Step 2: prices that maximize expected profit per customer, each within +/-20% of the current price.
# Usage: Rscript analysis.R <choices.csv> <costs.csv> [results.json]
library(nloptr)

args <- commandArgs(trailingOnly = TRUE)
ch   <- read.csv(args[1])                     # one row per customer and option; product_id 0 = no purchase
cost <- read.csv(args[2]); cost <- cost[order(cost$product_id), ]
feat <- c("imported", "sizesmall", "below6month", "slowflow", "wideneck", "straightshape")
J <- 15

# ---- Step 1: demand -------------------------------------------------------
# Utility of product j: alpha_j + (beta + sum_k gamma_k * feature_jk) * price_j. No purchase: 0.
cust <- as.integer(factor(ch$cust_id)); n <- max(cust)
X <- cbind(ch$price, ch$price * as.matrix(ch[, feat]))            # price and price x feature
D <- outer(ch$product_id, 1:J, "==") * 1                          # product intercepts
Z <- cbind(D, X)
negLL <- function(theta) {
  u <- as.vector(Z %*% theta)
  -(sum(u[ch$chosen == 1]) - sum(log(rowsum(exp(u), cust))))
}
grad <- function(theta) {
  u <- as.vector(Z %*% theta); eu <- exp(u)
  p <- eu / rowsum(eu, cust)[cust]
  -colSums(Z * (ch$chosen - p))
}
fit <- optim(rep(0, J + 1 + length(feat)), negLL, grad, method = "BFGS", hessian = TRUE, control = list(maxit = 2000, reltol = 1e-12))
se <- sqrt(diag(solve(fit$hessian)))
alpha <- fit$par[1:J]                                             # 15 intercepts, one per product
gamma <- fit$par[(J + 1):length(fit$par)]; names(gamma) <- c("price", paste0("price:", feat))
beta_j <- as.vector(gamma[1] + as.matrix(cost[, feat]) %*% gamma[-1])   # price slope of each product

# ---- Step 2: prices -------------------------------------------------------
profit <- function(p) { e <- exp(alpha + beta_j * p); sum((p - cost$cost) * e / (1 + sum(e))) }
p0 <- as.vector(tapply(ch$price[ch$product_id > 0], ch$product_id[ch$product_id > 0], mean))
opt <- nloptr(x0 = p0, eval_f = function(p) -profit(p), lb = 0.8 * p0, ub = 1.2 * p0,
              opts = list(algorithm = "NLOPT_LN_COBYLA", xtol_rel = 1e-10, maxeval = 100000))
p1 <- opt$solution
share <- function(p) { e <- exp(alpha + beta_j * p); e / (1 + sum(e)) }

tab <- data.frame(product = 1:J, cost = cost$cost, price_now = p0, price_new = p1, change_pct = (p1 / p0 - 1) * 100,
                  slope = beta_j, share_now = share(p0) * 100, share_new = share(p1) * 100)
print(round(tab, 2))
cat(sprintf("Customers %d | logLik %.1f | profit per customer: now %.4f, new %.4f (%+.1f%%)\n", n, -fit$value, profit(p0), profit(p1), (profit(p1) / profit(p0) - 1) * 100))
res <- list(customers = n, loglik = -fit$value, buy_rate = mean(ch$chosen[ch$product_id > 0]) * nrow(ch[ch$product_id > 0, ]) / n,
            coef = as.list(gamma), se = as.list(setNames(se[(J + 1):length(se)], names(gamma))),
            profit_now = profit(p0), profit_new = profit(p1), buy_now = sum(share(p0)), buy_new = sum(share(p1)), products = tab)
if (length(args) > 2) writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = 8, pretty = TRUE), args[3])
