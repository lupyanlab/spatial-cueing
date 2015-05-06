library(car)

recode_cue_type_as_num <- function(cue_type) {
  car::recode(cue_type,
    "'frame'=-1; 'nocue'=0; 'sound'=1",
    as.factor.result = FALSE,
    as.numeric.result = TRUE)
}

recode_cue_type_contr_as_num <- function(cue_type_contr) {
  car::recode(cue_type_contr,
    "'frame_v_nocue'=")
}



jitter_cue_type_int_by_subj <- function(frame, jitter_amount = 0.1) {
  frame %>% group_by(subj_id) %>% mutate(
    cue_type_jit = cue_type_int + runif(1, -jitter_amount, jitter_amount)) %>%
  .[["cue_type_jit"]]
}

determine_trial_type <- function(frame) {
  trial_type_map <- data.frame(row.names = c("target_present", "response"),
      hit = c(TRUE, "go"),
      miss = c(TRUE, "nogo"),
      false_alarm = c(FALSE, "go"),
      pass = c(FALSE, "nogo")
    ) %>% t() %>% data.frame()
  
  trial_type_map$trial_type <- row.names(trial_type_map)
  row.names(trial_type_map) <- NULL
  
  trial_type_map <- trial_type_map %>% mutate(
      target_present = as.logical(target_present))
  
  trial_types <- frame %>% select(target_present, response) %>% 
    left_join(trial_type_map) %>%
    select(trial_type)
  trial_types[["trial_type"]]
}

label_trial_type <- function(frame) {
  factor(frame$trial_type, 
         levels = c("hit", "false_alarm", "miss", "pass"),
         labels = c("Hit", "False Alarm", "Miss", "Pass"))
}

label_flicker <- function(frame) {
  factor(frame$flicker, levels = c("on", "off"), labels = c("Flicker On", "Flicker Off"))
}

label_interval <- function(frame) {
  factor(frame$interval, levels = c(0.75, 0.10), labels = c("750 ms", "100 ms"))
}