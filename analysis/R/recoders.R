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
  mask_type_map <- data_frame(
    mask_type = c("mask", "nomask"),
    mask_c = c(-0.5, 0.5)
  )
  
  frame %>% left_join(mask_type_map)
}

recode_cue_validity <- function(frame) {
  poly_contr <- contr.poly(n = 3) %>% 
    as.data.frame %>%
    rename(cue_validity_lin = .L, cue_validity_quad = .Q) %>%
    mutate(cue_validity = c("valid", "neutral", "invalid"))
  
  frame %>% left_join(poly_contr)
}