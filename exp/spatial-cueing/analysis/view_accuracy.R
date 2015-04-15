#' Look for a cueing effect in accuracies
#' 
#' Pierce Edmiston

library(dplyr)
library(lme4)
library(AICcmodavg)
library(ggplot2)
library(scales)

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
                 response != "timeout")

# linear mixed effects model
cueing <- set_treatment_contrasts(cueing)
acc_cueing <- glmer(is_correct ~ cue_type + (cue_type|subj_id), data = cueing,
                    family = "binomial")
summary(acc_cueing)

# model predictions
newdata <- data.frame(cue_type = unique(cueing$cue_type))
predictions <- predictSE(acc_cueing, newdata = newdata, 
  type = "response", se = TRUE, print.matrix = T)

model_estimates <- predictions %>%
  as.data.frame(.) %>%
  rename(acc = fit, se = se.fit) %>%
  cbind(newdata, .)
levels(model_estimates$cue_type) <- c("nocue", "dot", "sound")

cueing <- cueing %>% mutate(
  cue_type_c = recode(cue_type, "'nocue'=-1; 'dot'=0; 'sound'=1", as.factor.result = F),
  cue_type_j = cue_type_c + runif(n = n(), min = -0.05, max = 0.05)
)
  
ggplot(cueing, aes(x = cue_type, y = is_correct)) +
  stat_summary(aes(group = subj_id, color = subj_id), fun.y = mean, geom = "point",
               position = position_jitter(width = 0.1, height = 0.0)) +
  geom_errorbar(aes(y = acc, ymin = acc - se, ymax = acc + se), 
    data = model_estimates, width = 0.2) +
  scale_x_discrete("Cue Type", 
    labels = c("No Cue", "\"X\" over target", "Verbal direction cue")) +
  scale_y_continuous("Accuracy", labels = percent) +
  theme(
    legend.position = "none"
  )

ggsave("./plots/view_accs.png")
