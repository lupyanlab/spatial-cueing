library(ggplot2)
library(scales)

create_line_groups <- function(cueing_effects) {
  with(cueing_effects, paste(term, flicker, sep = ":"))
}

scale_interval_axis <- scale_x_continuous("Target Onset", 
                                          breaks = c(0.00, 0.10, 0.75),
                                          labels = c("0 ms\n(cue offset)", "100 ms", "750 ms"))

scale_term_legend <- scale_color_discrete("Cue Type", labels = c("Frame", "Sound"))

label_flicker <- function(flicker) {
  factor(flicker, levels = c("on", "off"), labels = c("Flicker On", "Flicker Off"))
}
