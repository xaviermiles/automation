# Automation

## Files
The first script developed was _./scrape_all_infoshare.py_, which was a proof-of-concept to scrape every dataset off [Infoshare](http://infoshare.stats.govt.nz/) using a depth-first search of the HTML. The _get_infoshare_dataset_ function in _./utils.py_ is far easier to use, allowing you to specify the Infoshare dataset by name and variable-options to select.

Running _./get_covid_portal_raw.py_ retrieves some datasets for the COVID-19 Data Portal, from Infoshare and First Gas websites. This is useful because these datasets require a lot of website-navigating (ie. clicking, searching) to find and are not retrievable by simply using HTTP/HTTPS requests.

The _./api_checks/_ folder includes a Python script (_api_checks.py_) which can be run to check the equivalency of data scraped from Infoshare and the corresponding data from the Stats NZ OData API.
This should be run from with _./api_checks/_ as the current directory and it relies on an R script (_compare.R_) to do data wrangling and make comparisons.
This is being used to double-check the data uploaded to the API is correct.

## Set-up (for linux)
Make sure the local repo is included in PATH or PYTHONPATH (for Python importing).

Selenium (Python package) requires a browser and a webdriver - this repo uses Firefox + Geckodriver (could be use other combination but code might have to be changed).
[Original guide for installation.](https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu) First, download firefox:
```
sudo apt install firefox
```
Then, find the latest Geckodriver link from [here](https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu) and install:
```
wget <<https://github.com/.../geckodriver-v???-linux64.tar.gz>>
tar -xvzf geckdriver*
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
```
