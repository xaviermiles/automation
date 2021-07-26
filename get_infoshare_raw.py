# Gets the data for the COVID-19 portal that are sourced from Infoshare

import os
import re
import itertools
from datetime import datetime
from collections import OrderedDict
import pandas as pd
from bs4 import BeautifulSoup

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

import utils
   

# Functions to download arbitrary/specified dataset from infoshare
def navigate_to_dataset(driver, dataset_ref):
    category, group, dataset = dataset_ref
    try:
        category_elem = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
              "//a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest') "
              f"and contains(text(), '{category}')]"                             
            ))
        )
    except TimeoutException:
        raise TimeoutException(f"'{category}' folder not found.")
    category_elem.click()
    
    try:
        group_elem = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
                "//a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest') "
                    f"and contains(text(), '{group}')]"
            ))
        )
    except TimeoutException:
        raise TimeoutException(f"'{group}' folder not found.")
    group_elem.click()
    
    try:
        dataset_elem = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
                "//a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest')]"
                f"/u[contains(text(), '{dataset}')]"
            ))
        )
    except TimeoutException:
        raise TimeoutException(f"'{dataset}' link not found.")
    dataset_elem.click()
    
    return driver


def make_infoshare_selections(driver, title_to_options, dataset_name):
    """
    Selects infoshare options according to 'title_to_options' dictionary. Then
    downloads the dataset using download_dataset().
    """
    select_var_boxes = driver.find_elements_by_xpath(
        "//td[@class = 'FunctionalArea_SelectVariablesBlock']"
        "//td[contains(@id, 'headerRow')]"
    )
    for box in select_var_boxes:
        title = box.find_element_by_xpath("./h6").text
        options = title_to_options[title]
        select_elem = Select(box.find_element_by_xpath(
            "../../..//select[contains(@id, 'lbVariableOptions')]"
        ))
        
        options_dt_check = re.match('USE_LATEST_DATETIME<(.*)>', options[0])
        if options_dt_check:
            dt_format = options_dt_check.group(1)
            options_dt = [datetime.strptime(o.text, dt_format) 
                          for o in select_elem.options if o.text]
            latest_dt_str = datetime.strftime(max(options_dt), dt_format)
            select_elem.select_by_visible_text(latest_dt_str)
        else:
            for opt in options:
                select_elem.select_by_visible_text(opt)
    
    driver = download_dataset(driver, dataset_name)
    return driver


def download_dataset(driver, dataset_name):
    try:
        go = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID,
                'ctl00_MainContent_btnGo'
            ))
        )
    except TimeoutException:
        raise TimeoutException("Can't find the Go button.")
    go.click()
    # first 'pxtable' is data, second is metadata
    data = driver.find_element_by_xpath("//table[@class = 'pxtable']")
    data_soup = BeautifulSoup(data.get_attribute('outerHTML'), 'html.parser')
    data_df = pd.read_html(str(data_soup))[0]
    data_df.to_csv(f"{SAVE_DIR}/{dataset_name}.csv", index=False)

    return driver


def get_infoshare_dataset(dataset_ref, title_to_options, dataset_name):
    """
    To use most recent period for a 'Time' selection, set the corresponding
    value in 'title_to_options' dictionary to a list[str] of length one
    with the (single) element 'USE_LATEST_DATETIME<***>' where *** is the 
    datetime format of the infoshare options.
    
    dataset_name should not include file extension; this is added later (.csv)
    """
    print(dataset_name)
    driver = utils.get_firefox_driver(SAVE_DIR, ['text/csv'])
    driver.get("http://infoshare.stats.govt.nz/")
    driver = navigate_to_dataset(driver, dataset_ref)
    driver = make_infoshare_selections(driver, title_to_options, dataset_name)
    driver.quit()


# Functions to download specific datasets from infoshare
def get_air_cargo():
    dataset_to_info = {
        'Exports': [
            ('FOB (free on board) NZ$(000)', 'FOB_NZD'),
            ('Gross weight (tonnes)', 'GW_Tonnes')
        ],
        'Imports': [
            ('CIF (cost, insurance and freight) NZ$(000)', 'CIF_NZD'),
            ('Gross weight (tonnes)', 'GW_Tonnes')
        ]
    }
    for dataset, info in dataset_to_info.items():
        for observation, suffix in info:
            get_infoshare_dataset(
                dataset_ref=(
                    'Imports and exports',
                    'Overseas Cargo Statistics - OSC',
                    f'Total {dataset} by New Zealand Port (Monthly)'
                ),
                title_to_options={
                    'New Zealand Port': ['Christchurch Airport'],
                    'Observations': [observation],
                    'Time': ['USE_LATEST_DATETIME<%YM%m>']
                },
                dataset_name=f"air_cargo_{dataset}_{suffix}"
            )
            

def get_sea_cargo():
    dataset_to_info = {
        'Exports': [
            ('FOB (free on board) NZ$(000)', 'FOB_NZD'),
            ('Gross weight (tonnes)', 'GW_Tonnes')
        ],
        'Imports': [
            ('CIF (cost, insurance and freight) NZ$(000)', 'CIF_NZD'),
            ('Gross weight (tonnes)', 'GW_Tonnes')
        ]
    }
    for dataset, info in dataset_to_info.items():
        for observation, suffix in info:
            get_infoshare_dataset(
                dataset_ref=(
                    'Imports and exports',
                    'Overseas Cargo Statistics - OSC',
                    f'Total {dataset} by New Zealand Port (Monthly)'
                ),
                title_to_options={
                    'New Zealand Port': [
                        'Auckland (sea)','Lyttelton (sea)','Napier (sea)',
                        'Port Chalmers (sea)','Tauranga (sea)','Wellington (sea)'
                    ],
                    'Observations': [observation],
                    'Time': ['USE_LATEST_DATETIME<%YM%m>']
                },
                dataset_name=f"sea_cargo_{dataset}_{suffix}"
            )
            
            
def get_card_transaction_total_spend():
    for treatment in ['Actual','Seasonally adjusted']:
        get_infoshare_dataset(
            dataset_ref=(
                'Economic indicators',
                'Electronic Card Transactions (ANZSIC06) - ECT',
                'Total values - Electronic card transactions A/S/T by division (Monthly)'
            ),
            title_to_options={
                'Actual/Seasonally Adjusted/Trend': [treatment],
                'Division': ['Total'],
                'Time': ['USE_LATEST_DATETIME<%YM%m>']
            },
            dataset_name=f"card_transaction_total_spend_values_{treatment}"
        )
        
    get_infoshare_dataset(
        dataset_ref=(
            'Economic indicators',
            'Electronic Card Transactions (ANZSIC06) - ECT',
            'Number of electronic card transactions A/S/T by division (Monthly)'
        ),
        title_to_options={
            'Actual/Seasonally Adjusted/Trend': ['Actual'],
            'Division': ['Total'],
            'Time': ['USE_LATEST_DATETIME<%YM%m>']
        },
        dataset_name='card_transaction_total_spend_number_Actual'
    )
    
    
def get_card_transaction_spend_by_industry():
    treatments = ['Actual','Seasonally adjusted']
    for treatment in treatments:
        get_infoshare_dataset(
            dataset_ref=(
                'Economic indicators',
                'Electronic Card Transactions (ANZSIC06) - ECT',
                'Total values - Electronic card transactions A/S/T by division (Monthly)'
            ),
            title_to_options={
                'Actual/Seasonally Adjusted/Trend': [treatment],
                'Division': ['RTS total industries'],
                'Time': ['USE_LATEST_DATETIME<%YM%m>']
            },
            dataset_name=f"card_transaction_spend_by_industry_total_{treatment}"
        )

        industries = ['Services','Non-retail excl. services']
        for industry in industries:
            get_infoshare_dataset(
                dataset_ref=(
                    'Economic indicators',
                    'Electronic Card Transactions (ANZSIC06) - ECT',
                    'Values - Electronic card transactions A/S/T by industry group (Monthly)'
                ),
                title_to_options={
                    'Actual/Seasonally Adjusted/Trend': [treatment],
                    'Industry Group': [industry],
                    'Time': ['USE_LATEST_DATETIME<%YM%m>']
                },
                dataset_name=f"card_transaction_spend_by_industry_{industry}_{treatment}"
            )


if __name__ == "__main__":
    SAVE_DIR = os.path.join(os.getcwd(), 'covid_portal_raw', 'Infoshare') 
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    get_air_cargo()
    get_sea_cargo()
    get_card_transaction_total_spend()
    get_card_transaction_spend_by_industry()
    