library(car)

recode_missing_cue_type_as_nocue <- function(frame) {
  mutate(frame, cue_type = ifelse(cue_type == "", "nocue", cue_type))
}

recode_responses_as_int <- function(frame) {
  mutate(frame, response_b = recode(response, "'present'=1; 'absent'=0; 'timeout'=-1"))
}

set_treatment_contrasts <- function(frame) {
  frame$cue_type <- factor(frame$cue_type)
  
  # treatment contrasts are chosen by default, but
  # set them manually just to be sure
  treatment_contrast <- contr.treatment(n = c("nocue", "dot", "sound"), base = 1)
  contrasts(frame$cue_type) <- treatment_contrast
  
  levels(frame$cue_type) <- c("nocue", "dot", "sound")

  frame
}
