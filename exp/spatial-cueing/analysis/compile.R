compile <- function(data_directory, pattern) {
  fnames <- list.files(data_directory, pattern, full.names = TRUE)
  plyr::ldply(fnames, read.table, sep = '\t', header = TRUE,
              row.names = NULL, stringsAsFactors = FALSE)
}
