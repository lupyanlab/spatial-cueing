library(car)
library(dplyr)
library(ggplot2)
library(reshape2)

source("./analysis/compile.R")
source("./analysis/calculate_dprime.R")

spatial_cueing <- compile("data", pattern = "SPC1")
dprimes <- calculate_dprime(spatial_cueing, expected_num_trials = 200)

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
