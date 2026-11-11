# Which new tracks a label must promote: can a model find the hits before the market does?
# A hit is a track in the top quarter of popularity among the tracks released in the same year.
# (The popularity score favors recent tracks, so one cutoff for all years would mix "hit" with "new".)
# Models are fitted on releases from 2000 to 2021 and tested on releases of 2022 and 2023.
# Usage: Rscript analysis.R <tracks.csv> [results.json]     (a 25% random sample of the public file)
suppressMessages(library(randomForest))
args <- commandArgs(trailingOnly = TRUE)
d <- read.csv(args[1], stringsAsFactors = FALSE)
d <- d[!is.na(d$popularity) & !is.na(d$year), ]
cutoff <- tapply(d$popularity, d$year, quantile, 0.75); HIT <- as.list(cutoff)
d$hit <- as.integer(d$popularity >= cutoff[as.character(d$year)])

# Record of the artist BEFORE the year of the track: number of earlier tracks and share of them that were hits.
# Only earlier years are used, so the model sees nothing that the label does not know at release.
ay <- aggregate(cbind(n = 1, h = d$hit) ~ artist_name + year, d, sum)
ay <- ay[order(ay$artist_name, ay$year), ]
ay$prev_n <- ave(ay$n, ay$artist_name, FUN = function(v) cumsum(v) - v)
ay$prev_h <- ave(ay$h, ay$artist_name, FUN = function(v) cumsum(v) - v)
d <- merge(d, ay[, c("artist_name", "year", "prev_n", "prev_h")], by = c("artist_name", "year"), all.x = TRUE)
d$prev_n[is.na(d$prev_n)] <- 0; d$prev_h[is.na(d$prev_h)] <- 0
d$artist_tracks <- log1p(d$prev_n)
d$artist_hit_share <- ifelse(d$prev_n > 0, d$prev_h / d$prev_n, 0)
d$new_artist <- as.integer(d$prev_n == 0)
d$minutes <- pmin(d$duration_ms / 60000, 15)
d$genre <- factor(d$genre)

audio  <- c("danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo", "minutes", "mode")
artist <- c("artist_tracks", "artist_hit_share", "new_artist")
train <- d$year <= 2021; tr <- d[train, ]; te <- d[!train, ]
te$genre[!(te$genre %in% unique(tr$genre))] <- NA; te <- te[!is.na(te$genre), ]

f <- function(v) as.formula(paste("hit ~", paste(v, collapse = " + ")))
sets <- list(`Sound only` = audio, `Sound and genre` = c(audio, "genre"), `Sound, genre and the record of the artist` = c(audio, "genre", artist))
P <- lapply(sets, function(v) predict(glm(f(v), tr, family = binomial), te, type = "response"))
# The forest cannot take 82 genre levels, so genre enters as its hit rate in the training years.
gr <- tapply(tr$hit, tr$genre, mean); tr$genre_hit_rate <- as.vector(gr[as.character(tr$genre)]); te$genre_hit_rate <- as.vector(gr[as.character(te$genre)])
set.seed(12345); s <- sample(nrow(tr), 60000); rfv <- c(audio, artist, "genre_hit_rate")
rf <- randomForest(x = tr[s, rfv], y = factor(tr$hit[s]), ntree = 150, importance = TRUE)
P$`Random forest, all inputs` <- predict(rf, te[, rfv], type = "prob")[, "1"]

auc <- function(p, y) { r <- rank(p); n1 <- sum(y == 1); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * sum(y == 0)) }
y <- te$hit; base <- mean(y)
top <- function(p, share) { k <- ceiling(length(p) * share); i <- order(-p)[1:k]; c(picks = k, hits = sum(y[i]), precision = mean(y[i]) * 100, found = sum(y[i]) / sum(y) * 100) }
out <- do.call(rbind, lapply(names(P), function(m) { t10 <- top(P[[m]], 0.10); t1 <- top(P[[m]], 0.01)
  data.frame(model = m, auc = auc(P[[m]], y), picks = t10[["picks"]], hits = t10[["hits"]], precision = t10[["precision"]], lift = t10[["precision"]] / (base * 100), found = t10[["found"]], precision_top1 = t1[["precision"]]) }))
print(out, row.names = FALSE)

imp <- sort(importance(rf)[, "MeanDecreaseGini"], decreasing = TRUE)
grp <- cut(te$artist_hit_share + ifelse(te$new_artist == 1, -1, 0), c(-2, -0.5, 0.0001, 0.25, 0.5, 1), labels = c("New artist", "No earlier hit", "Up to 25% hits", "25% to 50% hits", "More than 50% hits"))
by_artist <- data.frame(group = levels(grp), tracks = as.vector(table(grp)), hit_rate = as.vector(tapply(y, grp, mean)) * 100)
g <- sort(tapply(te$hit, droplevels(te$genre), mean) * 100, decreasing = TRUE)
print(by_artist); print(round(imp / sum(imp) * 100, 1)[1:8])
res <- list(rows = nrow(d), train_rows = nrow(tr), test_rows = nrow(te), hit_rate = mean(d$hit) * 100, test_hit_rate = base * 100, cutoff = HIT, artists = length(unique(d$artist_name)), genres = nlevels(d$genre),
            models = out, importance = as.list(round(imp / sum(imp) * 100, 1)), by_artist = by_artist, top_genres = as.list(round(head(g, 5), 1)), bottom_genres = as.list(round(tail(g, 5), 1)))
if (length(args) > 1) writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, digits = 6, pretty = TRUE), args[2])
