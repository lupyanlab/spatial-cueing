library(dplyr)

recode_cue_type <- function(frame) {
  cue_type_map <- data_frame(
    cue_contrast = rep(c("word_arrow", "visual_auditory"), each = 2),
    cue_type = c("visual_word", "visual_arrow", "visual_word", "auditory_word"),
    cue_c = rep(c(-0.5, 0.5), times = 2)
  )
  
  frame %>% left_join(cue_type_map)
}

recode_mask_type <- function(frame) {
  mask_levels <- c("nomask", "mask")
  mask_type_map <- data_frame(
    mask_type = mask_levels,
    mask_c = c(-0.5, 0.5)
  )
  
  frame %>% 
    left_join(mask_type_map) %>%
    mutate(mask_type = factor(mask_type, levels = mask_levels))
}

recode_cue_validity <- function(frame) {
  poly_contr <- contr.poly(n = 3) %>% 
    as.data.frame %>%
    rename(cue_effect_lin = .L, cue_effect_quad = .Q) %>%
    mutate(
      cue_validity = c("valid", "neutral", "invalid"),
      cue_effect_dodge = c(-0.1, 0.0, 0.1)
    )
  
  frame %>% left_join(poly_contr)
}