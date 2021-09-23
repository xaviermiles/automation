# Functions for comparing API to Infoshare datasets
suppressPackageStartupMessages({
  library(tidyverse)
  library(lubridate)
  library(zoo)
  library(jsonlite)
  library(optparse)
})

parse_yearmon_str <- function(yearmon_str) {
  yearmon_str %>% as.yearmon(format = "%YM%m") %>% as.Date(frac = 1)
}
parse_yearqtr_str <- function(yearqtr_str) {
  yearqtr_str %>% as.yearqtr(format = "%YQ%q") %>% as.Date(frac = 1)
}
parse_year_str <- function(year_str) {
  year_str %>% paste0(year_str, "-12-31") %>% ymd()
}

parse_period_col <- function(period_col) {
  # Returns final date in the given period (to align with API)
  if (grepl("\\d{4}M\\d{2}", period_col[1])) {
    parse_func <- parse_yearmon_str
  } else if (grepl("\\d{4}Q\\d", period_col[1])) {
    parse_func <- parse_func <- parse_yearqtr_str
  } else if (grepl("\\d{4}", period_col[1])) {
    parse_func <- parse_year_str
  }
  date_col <- as_date(map_dbl(period_col, parse_func))
  return(date_col)
}

parse_value_for_number <- function(raw_value) {
  raw_value %>%
    strsplit(" ") %>%
    unlist(.) %>%
    .[1] %>%
    gsub(",", "", .) %>%
    as.numeric() %>%
    suppressWarnings()
}

compare <- function(api_fpath, infoshare_fpath) {
  api_copy <- api_fpath %>%
    read_csv(col_types = cols()) %>%
    select_if(function(x) {!all(is.na(x))})   # remove all-NA columns
  
  num_header_rows <- names(api_copy) %>%
    str_extract("Label\\d") %>%
    na.omit() %>%
    length()
  
  infoshare <- infoshare_fpath %>%
    read_csv(col_types = cols())
  # Pivot Infoshare dataset from multi-level-header wide dataset to long format.
  # NB: Filters out any non-confidential ('C') rows with Value = NA as the API 
  # copy omits these rows for simplicity.
  names(infoshare) <-
    lapply(1:num_header_rows, function(i) {as_vector(infoshare[i, -1])}) %>%
    c(., sep = "__") %>%
    do.call(paste, .) %>%
    c("Period", .)
  infoshare <- infoshare[-(1:num_header_rows), ]
  infoshare_long <- infoshare %>%
    gather(variable, Value, -Period) %>%
    separate(variable, paste0("Label", 1:num_header_rows), sep="__") %>%
    mutate(
      Period = parse_period_col(Period),
      Status = Value %>%
        map_chr(function(v) { unlist(strsplit(v, " "))[2] }) %>%
        replace_na("F"),
      Value = map_dbl(Value, parse_value_for_number)
    ) %>%
    filter(!is.na(Value) | Status == "C")
  
  # Write long to csv
  infoshare_fpath %>%
    gsub(".csv", "__long.csv", .) %>%
    write_csv(infoshare_long, .)
  
  # Check equivalency of dataframes
  api_subset <- api_copy[, names(infoshare_long)]
  diff = setdiff(api_subset, infoshare_long)
  equivalent = (nrow(api_subset) == nrow(infoshare_long) && nrow(diff) == 0)

  return(equivalent)
}
