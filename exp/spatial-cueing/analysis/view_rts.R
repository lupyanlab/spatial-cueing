#' Look for a cueing effect in RTs
#' 
#' Pierce Edmiston

library(dplyr)
library(lme4)
library(AICcmodavg)
library(ggplot2)

source("./analysis/loaders.R")
source("./analysis/recoders.R")
source("./analysis/filters.R")

spatial_cueing <- compile(data_directory = "data", pattern = "SPC2")

# recode variables
spatial_cueing <- recode_missing_cue_type_as_nocue(spatial_cueing)
spatial_cueing <- recode_responses_as_int(spatial_cueing)

# drop practice trials, timeout trials, and incorrect response trials
cueing <- filter(spatial_cueing, 
                 part != "practice", 
                 response != "timeout",
                 is_correct == 1,
                 rt > 200.0)

# linear mixed effects model
cueing <- set_treatment_contrasts(cueing)
rt_cueing <- lmer(rt ~ cue_type + (cue_type|subj_id), data = cueing)
summary(rt_cueing)
summary(lmerTest::lmer(rt ~ cue_type + (cue_type|subj_id), data = cueing))

# model predictions
newdata <- data.frame(cue_type = unique(cueing$cue_type))
predictions <- predictSE(rt_cueing, newdata = newdata, 
                         type = "response", se = TRUE, print.matrix = T)

model_estimates <- predictions %>%
  as.data.frame(.) %>%
  rename(rt = fit, se = se.fit) %>%
  cbind(newdata, .)
levels(model_estimates$cue_type) <- c("nocue", "dot", "sound")

ggplot(cueing, aes(x = cue_type, y = rt)) +
  geom_violin(aes(fill = cue_type), alpha = 0.4) +
  geom_point(data = model_estimates) +
  geom_errorbar(aes(ymin = rt - se, ymax = rt + se), 
                data = model_estimates, width = 0.2) +
  scale_x_discrete("Cue Type", 
                   labels = c("No Cue", "\"X\" over target", "Verbal direction cue")) +
  scale_y_continuous("Reaction Time (ms)") +
  theme(
    legend.position = "none"
  )

ggsave("./plots/view_rts.png")
