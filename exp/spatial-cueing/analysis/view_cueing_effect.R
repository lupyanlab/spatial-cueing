library(car)
library(dplyr)
library(ggplot2)

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

tallies <- cueing %>% 
  group_by(subj_id, cue_type, cue_present, target_present, response) %>%
  summarize(num_trials = n())

expected_cells <- expand.grid(response = 0:1, target_present = 0:1, cue_present = 0:1)