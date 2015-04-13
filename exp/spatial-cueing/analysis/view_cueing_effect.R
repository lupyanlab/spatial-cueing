library(car)
library(dplyr)
library(ggplot2)
library(reshape2)

source("./analysis/compile.R")
spatial_cueing <- compile("data", pattern = "SPC1")

all_cueing <- filter(spatial_cueing, part == "cueing_effect")

num_cueing_trials <- 200
cueing <- all_cueing %>%
  group_by(subj_id) %>%
  filter(n() == num_cueing_trials,
         response != "timeout")

cueing <- cueing %>% mutate(
  cue_type = ifelse(cue_type == "", "nocue", cue_type),
  response = recode(response, "'present'=1; 'absent'=0")
)

# tally trials in each cell
# ----
tallies <- cueing %>%
  group_by(subj_id, cue_type, cue_present, target_present, response) %>%
  summarize(num_trials = n())

counts <- tallies %>% group_by(subj_id, cue_type, cue_present) %>%
  filter(response == 1) %>%
  dcast(subj_id + cue_type ~ target_present, value.var = "num_trials",
        fill = 0.0) %>%
  rename(hits = `1`, alarms = `0`)

dprimes <- counts %>% mutate(
  total = alarms + hits,
  hit_rate = hits/total,
  false_alarm = alarms/total,
  d_prime = qnorm(hit_rate) - qnorm(false_alarm)
)

perfect_performance <- (dprimes$d_prime == Inf)
dprimes[perfect_performance, "d_prime"] = qnorm(.99) - qnorm(0.01)

# plot effect of cue on d prime
# ----

dprimes_plot <- dprimes %>% mutate(
  cue_type_c = recode(cue_type, "'nocue'=-0.5; 'dot'=0.5"),
  cue_type_j = cue_type_c + runif(n = n(), min = -0.05, max = 0.05)
)

ggplot(dprimes_plot, aes(x = cue_type_c, y = d_prime)) +
  geom_point(aes(x = cue_type_j), size = 3, shape = 1) +
  geom_line(aes(group = subj_id, x = cue_type_j)) +
  stat_summary(aes(group = cue_type), geom = "bar", fun.y = mean,
               alpha = 0.4) +
  scale_x_continuous(breaks = c(-0.5, 0.5), labels = c("nocue", "dot")) +
  coord_cartesian(xlim = c(-1.5, 1.5))
