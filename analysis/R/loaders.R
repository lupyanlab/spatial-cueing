library(dplyr)
library(purrr)
library(car)

#' Compile the raw data files into a data.frame.
#' Assumes all data files have their own headers.
#' @param data_directory, str
#' @param pattern, str regular expression
compile <- function(data_directory, pattern) {
  fnames <- list.files(data_directory, pattern, full.names = TRUE)
  plyr::ldply(fnames, read.table, sep = '\t', header = TRUE,
              row.names = NULL, stringsAsFactors = FALSE)
}

code_missing_cue_type_as_nocue <- function(cue_type) {
  ifelse(cue_type == "", "nocue", cue_type)
}

code_responses_as_binary <- function(response) {
  recode(response, "'go'=1; 'nogo'=0", as.numeric.result = TRUE)
}

get_spatial_cueing <- function(interval = 0.750, flicker = "on") {  
  # compile data files matching correct_pattern and add columns for between
  # subjects variables interval and flicker
  compile_experiment <- function(regex_pattern, interval, flicker) {
    spatial_cueing <- compile(data_directory = "../exp/data", pattern = as.character(regex_pattern))
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
  
  # SPC6 is weird...
  # The last column, interval, is unlabeled, which causes all colnames
  # to be off by one (and the first column is named "row.names")
  # The data all compiles though, so just compile it, and shift the 
  # column names before merging with the rest of the data
  spc6 <- compile_experiment("SPC6", interval = 0.1, flicker = "off")
  spc6 <- select(spc6, -interval, -flicker)
  
  new_colnames <- c(colnames(spc6)[2:length(colnames(spc6))], "interval")
  colnames(spc6) <- new_colnames
  spc6$flicker <- "off"
  
  spatial_cueing <- rbind_list(spatial_cueing, spc6)

  print('Coding variables...')
  spatial_cueing$cue_type <- code_missing_cue_type_as_nocue(spatial_cueing$cue_type)
  spatial_cueing$response_b <- code_responses_as_binary(spatial_cueing$response)
  
  print('Dropping practice trials...')
  cueing <- filter(spatial_cueing, part != "practice")
  
  cueing
}