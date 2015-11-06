# Compiles the data from all versions of the spatial cueing experiment
# and saves to .rda in the data/ directory.

library(dplyr)
library(purrr)
library(car)

# compile functions ------------------------------------------------------------

compile <- function(data_directory, pattern, sep = '\t') {
  fnames <- list.files(data_directory, pattern, full.names = TRUE)
  plyr::ldply(fnames, read.table, sep = sep, header = TRUE,
              row.names = NULL, stringsAsFactors = FALSE)
}

recode_missing_cue_type_as_nocue <- function(frame) {
  frame %>% mutate(cue_type = ifelse(cue_type == "", "nocue", cue_type))
}

recode_responses_as_binary <- function(frame) {
  recode_str <- "'go'=1; 'nogo'=0"
  frame %>% mutate(
    response_b = recode(response, recode_str, as.numeric.result = TRUE)
  )
}

recode_missing_target_loc_as_nocue <- function(frame) {
  frame %>% mutate(
    target_loc = ifelse(target_loc == "", "notarget", target_loc)
  )
}

# go/no-go ---------------------------------------------------------------------

get_spatial_cueing <- function(interval = 0.750, flicker = "on") {
  # compile data files matching correct_pattern and add columns for between
  # subjects variables interval and flicker
  compile_experiment <- function(regex_pattern, interval, flicker) {
    spatial_cueing <- compile(data_directory = "data-raw/go-nogo",
                              pattern = as.character(regex_pattern))
    spatial_cueing <- spatial_cueing %>%
      mutate(interval = interval, flicker = flicker)
    spatial_cueing
  }

  pattern_matcher <- data_frame(
    interval = c(0.750, 0.750, 0.100),
    flicker = c("on", "off", "on"),
    regex_pattern = c("SPC3?_3", "SPC4", "SPC5")
  )
  correct_patterns <- pattern_matcher[(pattern_matcher$interval %in% interval &
                                       pattern_matcher$flicker %in% flicker), ]

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

  spatial_cueing <- rbind_list(spatial_cueing, spc6) %>%
    recode_missing_cue_type_as_nocue %>%
    recode_responses_as_binary %>%
    recode_missing_target_loc_as_nocue %>%
    mutate(cue_validity = "valid")

  cueing <- filter(spatial_cueing, part != "practice")

  cueing
}

go_nogo <- get_spatial_cueing(interval = c(0.750, 0.100), flicker = c("on", "off"))

# twomask ----------------------------------------------------------------------
twomask <- compile("data-raw/twomask", pattern = "SPC", sep = ",")

# fourmask-longsoa -------------------------------------------------------------
fourmask_longsoa <- compile("data-raw/fourmask-longsoa", pattern = "P", sep = ",")

# fourmask-shortsoa ------------------------------------------------------------
fourmask_shortsoa <- compile("data-raw/fourmask-shortsoa", pattern = "SPC", sep = ",")

# combine all experiments into a single data.frame -----------------------------

go_nogo <- go_nogo %>%
  rename(
    cue_dir = cue_loc,
    response_type = response,
    trial = trial_ix,

    # This needs to be adjusted! In the go/no-go experiment, interval
    # was not the time between stimulus onsets. I *think* it was the
    # difference between cue offset and target onset. It should be adjustable
    # if you look back at the iohub experiment.
    soa = interval
  ) %>%
  mutate(
    experiment = "go_nogo",
    mask_type = ifelse(flicker == "on", "mask", "nomask"),
    cue_contrast = "auditory_peripheral",
    target_loc_x = NA,
    target_loc_y = NA,
    block = 1
  ) %>%
  select(-(date:part), -flicker, -mask_flicker, -target_opacity, -cue_present,
         -cue_pos_x, -cue_pos_y, -target_pos_x, -target_pos_y, -key,
         -target_present, -target_duration, -response_b)

twomask$experiment <- "twomask"
fourmask_longsoa$experiment <- "fourmask_longsoa"
fourmask_shortsoa$experiment <- "fourmask_shortsoa"

longsoa_experiments <- rbind_list(twomask, fourmask_longsoa) %>%
  mutate(
    soa = 0.75,
    target_loc_x = NA,
    target_loc_y = NA
  )

cue_location_experiments <- rbind_list(longsoa_experiments, fourmask_shortsoa) %>%
  select(-sona_experiment_code, -experimenter)

spatial_cueing <- rbind_list(go_nogo, cue_location_experiments) %>%
  select(
    # between-subject conditions
    experiment,
    cue_contrast,
    mask_type,

    # lab identifiers
    subj_id,

    # trial identifiers
    block,
    trial,

    # cue vars
    cue_type,
    cue_dir,
    cue_validity,

    # interval vars
    soa,

    # target vars
    target_loc,
    target_loc_x,
    target_loc_y,

    # response vars
    response_type,
    rt,
    is_correct
  )

devtools::use_data(spatial_cueing)
