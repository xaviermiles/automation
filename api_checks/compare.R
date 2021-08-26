# Checks if API and Infoshare versions are equivalent
library(tidyverse)
library(lubridate)

data_folder = "data/api_checks"
api_to_infoshare <- c(
  "ITM441AA.csv" = "tourism1.csv",
  "ITM441AA-All.csv" = "tourism-all.csv"
)

parse_yearmon_col <- function(yearmon_col) {
  yearmon_col %>%
    map_dbl(function(yearmon_str) {
      yearmon_str %>% paste0("M01") %>% strsplit("M") %>% ymd()
    }) %>%
    as_date() %>%
    ceiling_date("months") - days(1)
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

for (api_fname in names(api_to_infoshare)) {
  infoshare_fname = api_to_infoshare[api_fname]
  print(paste(api_fname, "=?=", infoshare_fname))
  
  api_copy <- api_fname %>%
    file.path(data_folder, .) %>%
    read_csv(col_types = cols()) %>%
    mutate(Period = as.Date(Period, "%d/%m/%Y"),
           Value = suppressWarnings(as.numeric(Value)))
  
  num_header_rows <- names(api_copy) %>%
    str_extract("Label\\d") %>%
    na.omit() %>%
    length()
  
  infoshare <- infoshare_fname %>%
    file.path(data_folder, .) %>%
    read_csv(col_types = cols())
  
  # Concatenate header rows into a single row
  names(infoshare) <-
    lapply(1:3, function(i) {as_vector(infoshare[i, -1])}) %>%
    c(., sep = "__") %>%
    do.call(paste, .) %>%
    c("Period", .)
  infoshare <- infoshare[-(1:num_header_rows), ]
  # Pivot to long format, then split raw-value into numeric-value and status.
  # Filter out any non-confidential ('C') rows with Value = NA as the API copy 
  # omits these rows for simplicity.
  infoshare_long <- infoshare %>%
    gather(variable, Value, -Period) %>%
    separate(variable, paste0("Label", 1:num_header_rows), sep="__") %>%
    mutate(Period = parse_yearmon_col(Period),
           Status = map_chr(Value, function(v) { unlist(strsplit(v, " "))[2] }) %>% 
             replace_na("F"),
           Value = map_dbl(Value, parse_value_for_number)) %>%
    filter(!is.na(Value) | Status == "C")
  
  # Write long to csv
  # infoshare_fname %>%
  #   gsub(".csv", "", .) %>%
  #   paste0("__long.csv") %>%
  #   file.path(data_folder, .) %>%
  #   write_csv(infoshare_long, .)
  
  # Check equivalency of dataframes
  api_subset <- api_copy[, names(infoshare_long)]
  diff = setdiff(api_subset, infoshare_long)
  print(nrow(api_subset) == nrow(infoshare_long) && nrow(diff) == 0)
}
