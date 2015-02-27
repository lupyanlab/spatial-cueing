library(plyr)

compile <- function(dir, key, headername) {
  fnames <- list.files(dir, key, full.names=TRUE)
  header <- read.table(headername, header=T, sep='\t')
  header <- names(header)
  ldply(fnames, read.table, sep='\t', header=F, col.names=header, 
        row.names=NULL, stringsAsFactors=F)
}
