library(AICcmodavg)

get_glmer_predictions <- function(mod, x_preds) {
  y_preds <- predictSE(accuracy_mod, x_preds, 
                       type = "response", se = TRUE, print.matrix = TRUE)
  
  predictions <- cbind(x_preds, y_preds) %>%
    rename(accuracy = fit, se = se.fit)
  
  predictions
}