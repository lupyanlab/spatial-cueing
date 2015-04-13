library(car)
library(dplyr)
library(ggplot2)
library(reshape2)

source("./analysis/compile.R")
source("./analysis/calculate_dprime.R")

spatial_cueing <- compile("data", pattern = "SPC2")
dprimes <- calculate_dprime(spatial_cueing, expected_num_trials = 360)

# plot effect of cue on d prime
# ----

dprimes_plot <- dprimes %>% mutate(
  cue_type_c = recode(cue_type, "'nocue'=-1; 'dot'=0; 'sound'=1"),
  cue_type_j = cue_type_c + runif(n = n(), min = -0.05, max = 0.05)
)

ggplot(dprimes_plot, aes(x = cue_type_c, y = d_prime)) +
  geom_point(aes(x = cue_type_j), size = 3, shape = 1) +
  geom_line(aes(group = subj_id, x = cue_type_j)) +
  stat_summary(aes(group = cue_type), geom = "bar", fun.y = mean,
               alpha = 0.4) +
  scale_x_continuous(breaks = c(-1, 0, 1), labels = c("nocue", "dot", "sound")) +
  coord_cartesian(xlim = c(-2, 2), ylim = c(-2, 5))
