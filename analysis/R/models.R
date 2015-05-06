library(AICcmodavg)
library(car)
library(reshape2)

create_cue_type_treatment_contrasts <- function(cue_type) {
  # create contrast variables to ease interpretation
  # AICcmodavg may require hard coded factors
  cbind(
    frame_v_nocue = recode(cue_type, "'frame'=1; else=0", as.factor.result = FALSE),
    sound_v_nocue = recode(cue_type, "'sound'=1; else=0", as.factor.result = FALSE)
  )
}

center_flicker <- function(flicker) {
  recode(flicker, "'on'=-0.5; 'off'=0.5",
         as.factor.result = FALSE, as.numeric.result = TRUE)
}

center_interval <- function(interval) {
  recode(interval, "0.75=-0.5; 0.10=0.5",
         as.factor.result = FALSE, as.numeric.result = TRUE)
}

get_glmer_predictions <- function(mod, x_preds) {
  y_preds <- predictSE(accuracy_mod, x_preds, 
                       type = "response", se = TRUE, print.matrix = TRUE)
  
  predictions <- cbind(x_preds, y_preds) %>%
    rename(accuracy = fit, se = se.fit)
  
  predictions
}