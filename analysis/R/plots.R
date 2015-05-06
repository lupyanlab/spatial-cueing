library(ggplot2)
library(scales)

source("R/recoders.R")

create_line_groups <- function(cueing_effects) {
  with(cueing_effects, paste(term, flicker, sep = ":"))
}

calculate_cueing_effects <- function(frame, measure_vars) {
  id_vars = c("flicker", "interval")
  
  frame %>% summarize(
    frame_v_nocue = accuracy[cue_type == "frame"] - accuracy[cue_type == "nocue"],
    sound_v_nocue = accuracy[cue_type == "sound"] - accuracy[cue_type == "nocue"]
  ) %>% melt(id.vars = id.vars, variable.name = "cue_type_contr", value.name = "cueing_effect")
}

scale_cue_type_int <- scale_x_continuous("Cue Type",
                                         breaks = c(-1, 0, 1),
                                         labels = c("frame", "no cue", "sound"))
by_subj_point_shape <- 1
by_subj_line_size <- 0.3

scale_interval_axis <- scale_x_continuous("Target Onset", 
                                          breaks = c(0.00, 0.10, 0.75),
                                          labels = c("0 ms\n(cue offset)", "100 ms", "750 ms"))

scale_term_legend <- scale_color_discrete("Cue Type", labels = c("Frame", "Sound"))

label_flicker <- function(flicker) {
  factor(flicker, levels = c("on", "off"), labels = c("Flicker On", "Flicker Off"))
}

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
