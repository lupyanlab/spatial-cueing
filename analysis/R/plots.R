library(ggplot2)
library(scales)

source("R/recoders.R")

scale_cue_type_int <- scale_x_continuous("Cue Type",
                                         breaks = c(-1, 0, 1),
                                         labels = c("frame", "no cue", "sound"))
by_subj_point_shape <- 1
by_subj_line_size <- 0.3

plot_acc_by_subj <- function(frame) {
  # place the cue types on the axis
  frame$cue_type_int <- recode_cue_type_as_int(frame)
  frame$cue_type_jit <- jitter_cue_type_int_by_subj(frame)
  
  ggplot(frame, aes(x = cue_type_int, y = accuracy)) +
    geom_point(aes(x = cue_type_jit, color = subj_id), shape = by_subj_point_shape) + 
    geom_line(aes(x = cue_type_jit, color = subj_id), size = by_subj_line_size) +
    scale_cue_type_int +
    scale_y_continuous("Accuracy", labels = percent) +
    theme(legend.position = "none")
}
