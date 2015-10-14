library(dplyr)
library(ggplot2)
library(lme4)
library(AICcmodavg)

source("R/loaders.R")
source("R/recoders.R")

spc <- compile("data/", pattern = "SPC", sep = ",") %>%
  filter(block != 0) %>%
  mutate(
    rt = ifelse(is_correct, rt, NA),
    is_correct = ifelse(response_type == "timeout", NA, is_correct)
  ) %>%
  recode_cue_type %>%
  recode_cue_validity %>%
  recode_mask_type

# used to get error from predictSE
x_preds <- unique(spc[,c("cue_type", "cue_validity", "mask_c")]) %>%
  recode_cue_type %>%
  recode_cue_validity %>%
  recode_mask_type

# RTs
rt_plot <- ggplot(spc, aes(x = cue_type, y = rt, color = cue_validity)) +
  geom_point(position = position_jitter(width = 0.2), alpha = 0.4, size = 1) +
  facet_wrap("mask_type")
rt_plot

rt_mod <- lmer(rt ~ mask_c * cue_c * (cue_validity_lin + cue_validity_quad) + 
              (cue_validity_lin + cue_validity_quad|subj_id),
            data = spc)
summary(rt_mod)

rt_preds <- predictSE(rt_mod, x_preds, se = TRUE) %>%
  as.data.frame %>%
  rename(rt = fit, se = se.fit) %>%
  cbind(x_preds, .)

rt_plot +
  geom_pointrange(aes(ymin = rt - se, ymax = rt + se), position = "dodge", data = rt_preds) +
  coord_cartesian(ylim = c(200, 800))

# Accuracy
acc_plot <- ggplot(spc, aes(x = cue_type, y = is_correct, color = cue_validity)) +
  geom_point(position = position_jitter(height = 0.1, width = 0.2), alpha = 0.4, size = 1) +
  facet_wrap("mask_type")
acc_plot

acc_mod <- glmer(is_correct ~ mask_c * cue_c * (cue_validity_lin + cue_validity_quad) + 
              (cue_validity_lin + cue_validity_quad|subj_id),
            data = spc, family = binomial)
summary(acc_mod)

acc_preds <- predictSE(acc_mod, x_preds, se = TRUE) %>%
  as.data.frame %>%
  rename(is_correct = fit, se = se.fit) %>%
  cbind(x_preds, .)

acc_plot +
  geom_pointrange(aes(ymin = is_correct - se, ymax = is_correct + se), position = "dodge", data = acc_preds) +
  coord_cartesian(ylim = c(0.8, 1.0))