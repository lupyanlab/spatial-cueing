library(dplyr)

#' Compile the raw data files into a data.frame.
#' Assumes all data files have their own headers.
#' @param data_directory, str
#' @param pattern, str regular expression
compile <- function(data_directory, pattern) {
  fnames <- list.files(data_directory, pattern, full.names = TRUE)
  plyr::ldply(fnames, read.table, sep = '\t', header = TRUE,
              row.names = NULL, stringsAsFactors = FALSE)
}

get_spatial_cueing <- function() {
  status <- 'Compiling raw data...'
  print(status)
  
  spatial_cueing <- compile(data_directory = "data", pattern = "SPC3?_3")
  
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