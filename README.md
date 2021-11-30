# Automation

## Files
The _infoshare/_ folder has a module (_download.py_) with functions for downloading specified datasets from [Infoshare](http://infoshare.stats.govt.nz/).
This folder also includes a proof-of-concept/WIP script that downloads every Infoshare dataset, which uses a depth-first search of HTML to identify dataset names and then uses functions in _download.py_ to handle the downloading.

Running _get_covid_portal_raw.py_ retrieves some datasets for the COVID-19 Data Portal, from Infoshare and First Gas websites. This is useful because these datasets require a lot of website-navigating (ie. clicking, searching) to find and are not retrievable by simply using HTTP/HTTPS requests.

The _api_checks/_ folder includes a Python script (_api_checks.py_) which can be run to check the equivalency of data scraped from Infoshare and the corresponding data from the Stats NZ OData API.
This relies on R scripts/functions (_compare.R_, _compare_funcs.R_) to do data wrangling and make comparisons.
This is being used to double-check the data uploaded to the API is correct.

The _standalones/_ folder is for Python scripts that have been adapted to include no local imports (ie. self-contained).

**Note:** Any Python scripts should be run with their directory as the current working directory.
For example, _infoshare/scrape_all_infoshare.py_ should be run with _infoshare/_ as the working directory.

## Set-up
Make sure the local repo is included in PATH or PYTHONPATH (for Python importing).

Selenium (Python package) requires a browser and a webdriver. This repo supports Firefox + Geckodriver or Chrome + Chromedriver.

#### Firefox on Linux
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

#### Chrome on (deb-based) Linux:
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
