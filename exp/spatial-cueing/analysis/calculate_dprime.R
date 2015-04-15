
calculate_dprime <- function(frame, expected_num_trials) {
  all_cueing <- filter(frame, part == "cueing_effect")
  
  num_cueing_trials <- expected_num_trials
  cueing <- all_cueing %>%
    group_by(subj_id) %>%
    filter(n() == num_cueing_trials,
           response != "timeout")
  
  cueing <- recode_missing_cue_type_as_nocue(cueing)
  cueing <- recode_responses_as_int(cueing)
  
  # tally trials in each cell
  # ----
  tallies <- cueing %>%
    group_by(subj_id, cue_type, cue_present, target_present, response_b) %>%
    summarize(num_trials = n())
  
  counts <- tallies %>% group_by(subj_id, cue_type, target_present) %>%
    filter(response_b == 1) %>%
    dcast(subj_id + cue_type ~ target_present, value.var = "num_trials",
          fill = 0.0) %>%
    rename(hits = `1`, alarms = `0`)
  
  dprimes <- counts %>% mutate(
    total = alarms + hits,
    hit_rate = hits/total,
    false_alarm = alarms/total,
    d_prime = qnorm(hit_rate) - qnorm(false_alarm)
  )
  
  perfect_performance <- (dprimes$d_prime == Inf)
  dprimes[perfect_performance, "d_prime"] = qnorm(.99) - qnorm(0.01)
  
  awful_performance <- (dprimes$d_prime == -Inf)
  dprimes <- filter(dprimes, !awful_performance)
  
  dprimes
}
