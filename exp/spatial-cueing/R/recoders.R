library(car)

recode_missing_cue_type_as_nocue <- function(frame) {
  mutate(frame, cue_type = ifelse(cue_type == "", "nocue", cue_type))
}

recode_responses_as_int <- function(frame) {
  mutate(frame, response_b = recode(response, "'go'=1; 'nogo'=0"))
}

set_treatment_contrasts <- function(frame) {
  frame$cue_type <- factor(frame$cue_type, levels = c("nocue", "frame", "sound"))
  
  # treatment contrasts are chosen by default, but
  # set them manually just to be sure
  treatment_contrast <- contr.treatment(n = c("nocue", "frame", "sound"), base = 1)
  contrasts(frame$cue_type) <- treatment_contrast
  
  levels(frame$cue_type) <- c("nocue", "frame", "sound")
  
  # create contrast variables to ease interpretation
  # AICcmodavg may require hard coded factors
  frame <- frame %>% mutate(
    frame_v_nocue = car::recode(cue_type, "'frame'=1; else=0", as.factor.result = FALSE),
    sound_v_nocue = car::recode(cue_type, "'sound'=1; else=0", as.factor.result = FALSE)
  )

  frame
}

recode_cue_type_as_int <- function(frame) {
  car::recode(frame$cue_type,
    "'frame'=-1; 'nocue'=0; 'sound'=1",
    as.factor.result = FALSE,
    as.numeric.result = TRUE)
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