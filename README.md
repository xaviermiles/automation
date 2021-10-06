# Automation

## Files
The _infoshare/_ folder has a module (_download.py_) with functions for downloading specified datasets from [Infoshare](http://infoshare.stats.govt.nz/).
This folder also includes a proof-of-concept/WIP script that downloads every Infoshare dataset, which uses a depth-first search of HTML to identify dataset names and then uses functions in _download.py_ to handle the downloading.

Running _get_covid_portal_raw.py_ retrieves some datasets for the COVID-19 Data Portal, from Infoshare and First Gas websites. This is useful because these datasets require a lot of website-navigating (ie. clicking, searching) to find and are not retrievable by simply using HTTP/HTTPS requests.

The _api_checks/_ folder includes a Python script (_api_checks.py_) which can be run to check the equivalency of data scraped from Infoshare and the corresponding data from the Stats NZ OData API.
This relies on an R script (_compare.R_) to do data wrangling and make comparisons.
This is being used to double-check the data uploaded to the API is correct.

**Note:** Any Python scripts should be run with their directory as the current working directory.
For example, _infoshare/scrape_all_infoshare.py_ should be run with _infoshare/_ as the working directory.

## Set-up
Make sure the local repo is included in PATH or PYTHONPATH (for Python importing).

Selenium (Python package) requires a browser and a webdriver.

For getting the Firefox webdriver (Geckodriver) on linux, find the latest release from [here](https://github.com/mozilla/geckodriver/releases) and install by running:
```
wget <<https://github.com/.../geckodriver-v???-linux64.tar.gz>>
tar -xvzf geckdriver-v???-linux64.tar.gz
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
```

**NOTE: utils.get_chrome_driver function has not been tested yet**
