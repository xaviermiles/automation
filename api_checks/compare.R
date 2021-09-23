#!/usr/bin/env Rscript
# Callable-script which checks if API and Infoshare datasets are equivalent
# This essentically acts as the bridge between the Python and R code

source("compare_funcs.R")

# Read command line arguments
args_list <- list(
  make_option(c("-d", "--data_folder"), type="character", default=NULL, 
              help="directory where the files are saved", 
              metavar="character"),
  make_option(c("-c", "--datasets_info"), type="character", default=NULL, 
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
  { datasets_info <- fromJSON(cmd_line_args$datasets_info) },
  error = function(e) {stop("'--datasets_info' should be a JSON-style string")}
)
# TODO: check JSON structure
# if (???) {
#   stop("'--comparisons' JSON-string is incorrectly formatted")
# }

results = list()
for (dataset_name in names(datasets_info)) {
  api_fpath <- datasets_info[[dataset_name]][['api_fname']] %>%
    file.path(data_folder, .)
  infoshare_fpath <- datasets_info[[dataset_name]][['infoshare_fname']] %>%
    file.path(data_folder, .)
  
  equivalent <- compare(api_fpath, infoshare_fpath)
  
  results[[dataset_name]] <- list(
    api_fname = datasets_info[[dataset_name]][['api_fname']],
    infoshare_fname = datasets_info[[dataset_name]][['infoshare_fname']],
    equivalent = equivalent
  )
}

# Output results to stdout
print(toJSON(results, auto_unbox=TRUE))
