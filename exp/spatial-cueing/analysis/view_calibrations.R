library(zoo)
library(dplyr)
library(ggplot2)

source("./analysis/compile.R")

calibrations <- compile("calibration", key = "SPC", 
                        headername = "calibration-header.txt")

calibrations <- calibrations %>% group_by(subj_code) %>%
  mutate(rolling = rollmean(accuracy, k = 5, fill = NA))

# should converge
ggplot(calibrations, aes(x = trial_ix, y = rolling, group = subj_code)) +
  geom_line(aes(color = subj_code)) +
  geom_hline(yintercept = 0.6, lty = 2)

# doesn't need to converge, just needs to stabilize
ggplot(calibrations, aes(x = trial_ix, y = opacity, group = subj_code)) +
  geom_line(aes(color = subj_code))
