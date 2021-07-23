import os
import re
import itertools
from datetime import datetime
from collections import OrderedDict
import pandas as pd
from bs4 import BeautifulSoup

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

import utils
   

# Functions to download arbitrary/specified dataset from infoshare
def navigate_to_dataset(driver, dataset_ref):
    category, group, dataset = dataset_ref
    try:
        category_elem = driver.find_element_by_xpath(
            "//a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest') "
                f"and contains(text(), '{category}')]"
        )
    except NoSuchElementException:
        err_msg = f"'{category}' folder not found."
        raise NoSuchElementException(err_msg)
    category_elem.click()
    
    try:
        group_elem = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
                "//a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest') "
                    f"and contains(text(), '{group}')]"
            ))
        )
    except TimeoutException:
        err_msg = f"'{group}' folder not found."
        raise TimeoutException(err_msg)
    group_elem.click()
    
    try:
        dataset_elem = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
                "//a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest')]"
                f"/u[contains(text(), '{dataset}')]"
            ))
        )
    except TimeoutException:
        err_msg = f"'{dataset}' link not found."
        raise TimeoutException(err_msg)
    dataset_elem.click()
    
    return driver


def make_infoshare_selections(driver, title_to_option, dataset_name):
    """
    Selects infoshare options according to 'title_to_option' dictionary.
    """
    select_var_boxes = driver.find_elements_by_xpath(
        "//td[@class = 'FunctionalArea_SelectVariablesBlock']"
        "//td[contains(@id, 'headerRow')]"
    )
    for box in select_var_boxes:
        title = box.find_element_by_xpath("./h6").text
        option = title_to_option[title]
        select_elem = Select(box.find_element_by_xpath(
            "../../..//select[contains(@id, 'lbVariableOptions')]"
        ))
        
        option_dt_check = re.match('USE_LATEST_DATETIME<(.*)>', option)
        if option_dt_check:
            dt_format = option_dt_check.group(1)
            options_dt = [datetime.strptime(o.text, dt_format) 
                          for o in select_elem.options if o.text]
            latest_dt_str = datetime.strftime(max(options_dt), dt_format)
            select_elem.select_by_visible_text(latest_dt_str)
        else:
            select_elem.select_by_visible_text(option)
    
    driver = download_dataset(driver, dataset_name)
    return driver


def download_dataset(driver, dataset_name):
    driver.find_element_by_xpath(
        "//input[@id = 'ctl00_MainContent_btnGo']"
    ).click()
    # first 'pxtable' is data, second is metadata
    data = driver.find_element_by_xpath("//table[@class = 'pxtable']")
    data_soup = BeautifulSoup(data.get_attribute('outerHTML'), 'html.parser')
    data_df = pd.read_html(str(data_soup))[0]
    data_df.to_csv(f"{SAVE_DIR}/{dataset_name}.csv", index=False)

    return driver


def get_infoshare_dataset(dataset_ref, title_to_options):
    print('--'.join(dataset_ref))
    option_combinations = list(itertools.product(*title_to_options.values()))
    
    # Download the data for each combination of selection options
    # NB: title_to_options[str -> list[str]] VERSUS title_to_option[str -> str]
    for i, comb in enumerate(option_combinations):
        print(i)
        driver = utils.get_firefox_driver(SAVE_DIR, ['text/csv'])
        driver.get("http://infoshare.stats.govt.nz/")
        driver = navigate_to_dataset(driver, dataset_ref)

        title_to_option = OrderedDict({
            k: v for k, v in zip(title_to_options.keys(), comb)
        })
        dataset_name = '__'.join([dataset_ref[-1]] + list(comb))
        driver = make_infoshare_selections(driver, title_to_option, dataset_name)

        driver.quit()


# Functions to download specific datasets from infoshare
def get_cargo_exports():
    get_infoshare_dataset(
        dataset_ref = (
            'Imports and exports',
            'Overseas Cargo Statistics - OSC',
            'Total Exports by New Zealand Port (Monthly)'),
        title_to_options = OrderedDict({
            'New Zealand Port': ['Christchurch Airport'],
            'Observations': ['FOB (free on board) NZ$(000)','Gross weight (tonnes)'],
            'Time': ['USE_LATEST_DATETIME<%YM%m>']
        })
    )


def get_cargo_imports():
    get_infoshare_dataset(
        dataset_ref = (
            'Imports and exports',
            'Overseas Cargo Statistics - OSC',
            'Total Imports by New Zealand Port (Monthly)'),
        title_to_options = OrderedDict({
            'New Zealand Port': ['Christchurch Airport'],
            'Observations': ['CIF (cost, insurance and freight) NZ$(000)','Gross weight (tonnes)'],
            'Time': ['USE_LATEST_DATETIME<%YM%m>']
        })
    )


if __name__ == "__main__":
    SAVE_DIR = os.path.join(os.getcwd(), 'covid_portal_raw', 'Infoshare') 
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    get_cargo_exports()
    get_cargo_imports()
    