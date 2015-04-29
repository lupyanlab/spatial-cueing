library(dplyr)
library(purrr)

#' Compile the raw data files into a data.frame.
#' Assumes all data files have their own headers.
#' @param data_directory, str
#' @param pattern, str regular expression
compile <- function(data_directory, pattern) {
  fnames <- list.files(data_directory, pattern, full.names = TRUE)
  plyr::ldply(fnames, read.table, sep = '\t', header = TRUE,
              row.names = NULL, stringsAsFactors = FALSE)
}

get_spatial_cueing <- function(interval = 0.750, flicker = "on") {  
  # compile data files matching correct_pattern and add columns for between
  # subjects variables interval and flicker
  compile_experiment <- function(regex_pattern, interval, flicker) {
    spatial_cueing <- compile(data_directory = "data", pattern = as.character(regex_pattern))
    spatial_cueing <- mutate(spatial_cueing, interval = interval, flicker = flicker)
    spatial_cueing
  }

  pattern_matcher <- data_frame(
    interval = c(0.750, 0.750, 0.100), 
    flicker = c("on", "off", "on"),
    regex_pattern = c("SPC3?_3", "SPC4", "SPC5")
  )
  correct_patterns <- pattern_matcher[(pattern_matcher$interval %in% interval & 
                                       pattern_matcher$flicker %in% flicker), ]

  print('Compiling raw data...')
  spatial_cueing <- correct_patterns %>%
    split(.$regex_pattern) %>%
    map(~ compile_experiment(.$regex_pattern, .$interval, .$flicker)) %>%
    rbind_all(.)
  
  # handle exceptions
  spatial_cueing[spatial_cueing$subj_id %in% c("SPC504a", "SPC508"), "interval"] = 0.10

  # recode variables
  source("R/recoders.R")
  print('Recoding variables...')
  spatial_cueing <- recode_missing_cue_type_as_nocue(spatial_cueing)
  spatial_cueing <- recode_responses_as_int(spatial_cueing)
  
  # drop practice trials
  print('Dropping practice trials...')
  cueing <- filter(spatial_cueing, part != "practice")
  
  cueing
}