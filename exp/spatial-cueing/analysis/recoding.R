library(car)

recode_missing_cue_type_as_nocue <- function(frame) {
  mutate(frame, cue_type = ifelse(cue_type == "", "nocue", cue_type))
}

recode_responses_as_int <- function(frame) {
  mutate(frame, response = recode(response, "'present'=1; 'absent'=0"))
}
