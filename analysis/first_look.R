library(dplyr)
library(ggplot2)
library(lme4)
library(AICcmodavg)

source("R/loaders.R")
source("R/recoders.R")

spc <- compile("data/", pattern = "test_", sep = ",") %>%
  mutate(rt = ifelse(is_correct, rt, NA)) %>%
  recode_cue_type %>%
  recode_cue_validity %>%
  recode_mask_type

base_plot <- ggplot(spc, aes(x = cue_type, y = rt, color = cue_validity)) +
  geom_point(position = position_jitter(width = 0.2), alpha = 0.4, shape = 1, size = 1) +
  stat_summary(fun.y = mean, geom = "point", size = 3)
base_plot

mod <- lmer(rt ~ mask_c * cue_c * (cue_validity_lin + cue_validity_quad) + 
              (cue_validity_lin + cue_validity_quad|subj_id),
            data = spc)
summary(mod)

x_preds <- unique(spc[,c("cue_type", "cue_validity", "mask_c")]) %>%
  recode_cue_type %>%
  recode_cue_validity %>%
  recode_mask_type
y_preds <- predictSE(mod, x_preds, se = TRUE) %>%
  rename(rt = fit, se = se.fit)
preds <- cbind(x_preds, y_preds)

base_plot +
  geom_errorbar(aes(ymin = rt - se, ymax = rt + se), data = preds, width = 0.3)
