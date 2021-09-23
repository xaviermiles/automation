#!/usr/bin/env Rscript
# Checks if API and Infoshare versions are equivalent
suppressPackageStartupMessages({
  library(tidyverse)
  library(lubridate)
  library(zoo)
  library(jsonlite)
  library(optparse)
})

# Helper functions
parse_period_col <- function(period_col) {
  # Returns final date in the given period (to align with API)
  if (grepl("\\d{4}M\\d{2}", period_col[1])) {
    # Monthly
    date_col <- map(period_col,
      function(yearmon_str) {
        yearmon_str %>% as.yearmon(format = "%YM%m") %>% as.Date(frac = 1)
      }
    )
  } else if (grepl("\\d{4}Q\\d", period_col[1])) {
    # Quarterly
    date_col <- map(period_col,
      function(yearqtr_str) {
        yearqtr_str %>% as.yearqtr(format = "%YQ%q") %>% as.Date(frac = 1)
      }
    )
  } else if (grepl("\\d{4}", period_col[1])) {
    # Annual
    date_col <- map(period_col,
      function(year_str) {
        ymd(paste0(year_str, "-12-31"))
      }
    )
  }
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

# Read command line arguments
args_list <- list(
  make_option(c("-d", "--data_folder"), type="character", default=NULL, 
              help="directory where the files are saved", 
              metavar="character"),
  make_option(c("-c", "--comparisons"), type="character", default=NULL, 
              help="json string with filenames for each dataset", 
              metavar="character")
)
cmd_line_args <- args_list %>%
  OptionParser(option_list=.) %>%
  parse_args()
data_folder <- cmd_line_args$data_folder
if (is.null(data_folder)) {
  stop("Please supply script argument: '--data_folder'")
}
tryCatch(
  { datasets_info <- fromJSON(cmd_line_args$comparisons) },
  error = function(e) {stop("'--comparisons' should be a JSON-style string")}
)
# TODO: check JSON structure
# if (???) {
#   stop("'--comparisons' JSON-string is incorrectly formatted")
# }

# Do comparing
results = list()
for (dataset_name in names(datasets_info)) {
  api_fname = datasets_info[[dataset_name]][['api_fname']]
  infoshare_fname = datasets_info[[dataset_name]][['infoshare_fname']]
  
  api_copy <- api_fname %>%
    file.path(data_folder, .) %>%
    read_csv(col_types = cols()) %>%
    mutate(
      Period = as.Date(Period, "%d/%m/%Y"),
      Value = suppressWarnings(as.numeric(Value))
    ) %>%
    select_if(function(x) {!all(is.na(x))})   # remove all-NA columns
  
  num_header_rows <- names(api_copy) %>%
    str_extract("Label\\d") %>%
    na.omit() %>%
    length()
  
  infoshare <- infoshare_fname %>%
    file.path(data_folder, .) %>%
    read_csv(col_types = cols())
  # Pivot Infoshare dataset from multi-level-header wide dataset to long format.
  # NB: Filters out any non-confidential ('C') rows with Value = NA as the API 
  # copy omits these rows for simplicity.
  names(infoshare) <-
    lapply(1:3, function(i) {as_vector(infoshare[i, -1])}) %>%
    c(., sep = "__") %>%
    do.call(paste, .) %>%
    c("Period", .)
  infoshare <- infoshare[-(1:num_header_rows), ]
  infoshare_long <- infoshare %>%
    gather(variable, Value, -Period) %>%
    separate(variable, paste0("Label", 1:num_header_rows), sep="__") %>%
    mutate(Period = parse_period_col(Period),
           Status = Value %>%
             map_chr(
               function(v) { unlist(strsplit(v, " "))[2] }
             ) %>% 
             replace_na("F"),
           Value = map_dbl(Value, parse_value_for_number)) %>%
    filter(!is.na(Value) | Status == "C")
  
  # Write long to csv
  infoshare_fname %>%
    gsub(".csv", "", .) %>%
    paste0("__long.csv") %>%
    file.path(data_folder, .) %>%
    write_csv(infoshare_long, .)
  
  # Check equivalency of dataframes
  api_subset <- api_copy[, names(infoshare_long)]
  diff = setdiff(api_subset, infoshare_long)
  equivalent = (nrow(api_subset) == nrow(infoshare_long) && nrow(diff) == 0)

  results[[dataset_name]] <- list(
    api_fname = api_fname,
    infoshare_fname = infoshare_fname,
    equivalent = equivalent
  )
}

# Return results
print(toJSON(results, auto_unbox=TRUE))
