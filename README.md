# Automation

## Files
`infoshare/`

- `download.py`: functions for downloading specified datasets from [Infoshare](http://infoshare.stats.govt.nz/)
- `scrape_all_infoshare.py`: proof-of-concept script that downloads every Infoshare dataset, which uses a depth-first search of HTML to identify dataset names and then uses functions in `download.py` to handle the downloading

`covid_portal/`

- `check_covid_portal.py`: checks the download on the COVID-19 data portal
- `check_covid_portal_standalone.py`: ditto, but has no dependencies on any other python files
- `get_covid_portal_raw.py`: scrapes some data for the portal

`api_checks/`

- `api_checks.py`: script to check the equivalency of data scraped from Infoshare and the corresponding data from the Stats NZ OData API
-  `compare.R` and `compare_funcs.R`: helper scripts/functions for data wrangling and making comparisons

`data_releases/`

- `daily_run.py`: WIP/mock schedule-able script that checks Outlook calendar for datasets pending supply, using scraping to check whether *new* data is available from the corresponding data supplier's website, and sending notification emails and removing calendar item if the dataset is ready to be downloaded
- `site_checking.py`: defines function to check data supplier website for *new* data
- `outlook.py`: helper functions to interact with Outlook email and calendar via O365 python package
- `stats_release_calendar.py`: scrapes Stats NZ release calendar

## Set-up
You must also have a file named "config.yaml" (at root of repository) controls some options for various functions/scripts in the repo.
See `config-schema.json` for an example config.
**The only required field is `webdriver.browser_to_use`, which can be "chrome" or "firefox".**

Make sure the local repo is included in PATH or PYTHONPATH (for Python importing).
Any Python scripts should be run with their directory as the current working directory.
For example, `infoshare/scrape_all_infoshare.py` should be run with `infoshare/` as the working directory.

Selenium (Python package) requires a browser and a webdriver. This repo supports Firefox + Geckodriver or Chrome + Chromedriver, which is specified in "config.yaml" as described above.

### Firefox on Linux
```
sudo apt install firefox
```
Find the latest release of geckodriver from [here](https://github.com/mozilla/geckodriver/releases). Suppose the latest version is v0.30.0, then run the following to install geckodriver install by running:
```
wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz
tar -xvzf geckdriver-v0.30.0-linux64.tar.gz
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
rm geckdriver-v0.30.0-linux64.tar.gz
```

### Chrome on (deb-based) Linux:
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
```
Find out the version of Chrome by running
```
google-chrome --version
```
and then need to install the corresponding version of chromedriver. Suppose Chrome was version 94.0.4606.71, then run the following to install chromedriver.
```
wget https://chromedriver.storage.googleapis.com/94.0.4606.71/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chown root:root /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver
```
