
calculate_dprime <- function(frame, expected_num_trials) {
  all_cueing <- filter(spatial_cueing, part == "cueing_effect")
  
  num_cueing_trials <- expected_num_trials
  cueing <- all_cueing %>%
    group_by(subj_id) %>%
    filter(n() == num_cueing_trials,
           response != "timeout")
  
  cueing <- cueing %>% mutate(
    cue_type = ifelse(cue_type == "", "nocue", cue_type),
    response = recode(response, "'present'=1; 'absent'=0")
  )
  
  # tally trials in each cell
  # ----
  tallies <- cueing %>%
    group_by(subj_id, cue_type, cue_present, target_present, response) %>%
    summarize(num_trials = n())
  
  counts <- tallies %>% group_by(subj_id, cue_type, cue_present) %>%
    filter(response == 1) %>%
    dcast(subj_id + cue_type ~ target_present, value.var = "num_trials",
          fill = 0.0) %>%
    rename(hits = `1`, alarms = `0`)
  
  dprimes <- counts %>% mutate(
    total = alarms + hits,
    hit_rate = hits/total,
    false_alarm = alarms/total,
    d_prime = qnorm(hit_rate) - qnorm(false_alarm)
  )
  
  perfect_performance <- (abs(dprimes$d_prime) == Inf)
  dprimes[perfect_performance, "d_prime"] = qnorm(.99) - qnorm(0.01)
  
  dprimes
}
