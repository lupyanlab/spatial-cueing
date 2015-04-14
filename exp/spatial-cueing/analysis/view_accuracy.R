#library(car)
library(dplyr)
library(ggplot2)
#library(reshape2)

source("./analysis/compile.R")
source("./analysis/calculate_dprime.R")
source("./analysis/recoding.R")

spatial_cueing <- compile("data", pattern = "SPC2")

cueing <- filter(spatial_cueing, 
                 part == "cueing_effect", 
                 response != "timeout")

cueing <- recode_missing_cue_type_as_nocue(cueing)

cueing %>% group_by(subj_id, cue_type) %>%
  summarize(accuracy = mean(is_correct))

cueing <- cueing %>% mutate(
  cue_type_c = recode(cue_type, "'nocue'=-1; 'dot'=0; 'sound'=1"),
  cue_type_j = cue_type_c + runif(n = n(), min = -0.05, max = 0.05)
)

ggplot(cueing, aes(x = cue_type_c, y = is_correct)) +
  stat_summary(aes(group = subj_id), fun.y = mean, geom = "point") +
  stat_summary(aes(group = subj_id), fun.y = mean, geom = "line")

