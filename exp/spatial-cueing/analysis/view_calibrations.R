library(zoo)
library(dplyr)
library(ggplot2)

source("./analysis/compile.R")
spatial_cueing <- compile("data", pattern = "SPC1")

all_calibrations <- filter(spatial_cueing, part == "calibration")

# some participants didn't complete all 120 calibration trials.
# remove them from the data
num_trials_expected <- 120
calibrations <- all_calibrations %>% 
  group_by(subj_id) %>%
  filter(n() == num_trials_expected) %>%
  ungroup()

rolling_accuracy <- calibrations %>% group_by(subj_id) %>%
  mutate(rolling = rollmean(is_correct, k = 20, fill = NA))

# should converge
ggplot(rolling_accuracy, aes(x = trial_ix, y = rolling, group = subj_id)) +
  geom_line(aes(color = subj_id)) +
  geom_hline(yintercept = 0.5, lty = 2) +
  stat_summary(aes(group = 1), fun.y = mean, geom = "line")

# doesn't need to converge, just needs to stabilize
ggplot(rolling_accuracy, aes(x = trial_ix, y = target_opacity, group = subj_id)) +
  geom_line(aes(color = subj_id))
