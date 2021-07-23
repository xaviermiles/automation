# There is three levels - type, group, dataset
# This script navigates all 3 levels to the next dataset and recursively breaks
# back up to the next level (and looks for next element) until there is no 
# first-level elements left.
# >> It is acting like a depth-first search <<

# To setup Firefox driver:
# https://askubuntu.com/questions/870530/how-to-install-geckodriver-in-ubuntu

import os
import csv
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

import utils


def get_num_fl_folders():
    driver = utils.get_firefox_driver(SAVE_DIR, ['text/csv'])
    driver.get("http://infoshare.stats.govt.nz/")
    num_fl_folders = len(driver.find_elements_by_xpath(
        "//div[@id = 'ctl00_MainContent_tvBrowseNodes']"
        "//td[@style]"
        "/a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest')]"
    ))
    driver.quit()
    return num_fl_folders


# Workhorse functions
def get_info_from_dataset(driver, tl_elem, dataset_name, save_dir):
    tl_elem.click()  # navigate to Search tab
    try:
        _ = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
                "//table[@id = 'navigation']"
            ))
        )
    except TimeoutException:
        raise NotImplementedError("page didn't load :(")
    
    select_all_ids = [e.get_attribute('id') for e in driver.find_elements_by_xpath(
        "//table[@id = 'ctl00_MainContent_tblVariableSelectors']"
        "//span[substring(@id, string-length(@id) - string-length('SelectAll') + 1) = 'SelectAll']"
    )]
    for select_all_id in select_all_ids:
        elem = driver.find_element_by_xpath(
            "//table[@id = 'ctl00_MainContent_tblVariableSelectors']"
            f"//span[@id = '{select_all_id}']"
        )
        elem.click()
    
    go_button = driver.find_element_by_xpath(
        "//input[@id = 'ctl00_MainContent_btnGo']"
    )
    go_button.click()  # navigate to View table page
    
    # Saves data and metadata together in one CSV:
#     save_dropdown = Select(driver.find_element_by_id('ctl00_MainContent_dlSaveOptions'))
#     save_dropdown.select_by_value('csv')
#     print('Downloaded CSV, ', end="")
#     # Change CSV to have meaningful (comes out coded by default)
#     fpath = max([f"{save_dir}/{f}" for f in os.listdir(save_dir)], key=os.path.getctime)
#     os.rename(fpath, f"{save_dir}/{dataset_name}.csv")
    
    # Save data and metdata in different files:
    tables = driver.find_elements_by_xpath("//table[@class = 'pxtable']")
    data = tables[0].get_attribute('outerHTML')
    data_soup = BeautifulSoup(data, 'html.parser')
    data_df = pd.read_html(str(data_soup))[0]
    data_df.to_csv(f"{save_dir}/{dataset_name}.csv")
    
    meta = tables[1].find_element_by_xpath(
        "//td[@class = 'footnote']"
    ).get_attribute('outerHTML')
    meta_soup = BeautifulSoup(meta, 'html.parser')
    meta_text = meta_soup.get_text(separator='\n')
    with open(f"{save_dir}/{dataset_name}__meta.txt", 'w') as f:
        f.write(meta_text)
    
    # Return to original page
    try:
        browse = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
                "//table[@id = 'navigation']"
                "//a[@id = 'ctl00_headerUserControl_browseHyperlink']"
            ))
        )
        browse.click()
    except TimeoutException:
        raise NotImplementedError("Can't find browse button.")
        
    return driver


def navigate_mainpage(save_dir):
    # Don't want to expand ALL folders in same driver instance because selenium
    # has a maximum scrolling ability, so a new driver/browser is used when
    # navigating each first-level folder.
    num_fl_folders = get_num_fl_folders()
    
    data_ids = []
    i = 0
    for fl_num in range(num_fl_folders):
        driver = utils.get_firefox_driver(SAVE_DIR, ['text/csv'])
        driver.get("http://infoshare.stats.govt.nz/")
        try:
            fl_elem = driver.find_element_by_xpath(
                "//div[@id = 'ctl00_MainContent_tvBrowseNodes']"
                f"//a[@id = 'ctl00_MainContent_tvBrowseNodest{i}']"
            )
        except NoSuchElementException:
            print('y1')
            break  # no more first-level elements
        fl_name = fl_elem.text
        print(i, fl_name)
        fl_elem.click()
        i = fl_num + 1

        while True:
            try:
                sl_elem = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//div[@id = 'ctl00_MainContent_tvBrowseNodes']"
                        f"/div[@id = 'ctl00_MainContent_tvBrowseNodesn{fl_num}Nodes']"
                        f"//a[@id = 'ctl00_MainContent_tvBrowseNodest{i}']"
                    ))
                )
            except TimeoutException:
                print('y2')
                break  # no more second-level elements
            sl_name = sl_elem.text
            print(f"  > {sl_name}:", end=' ', flush=True)
            sl_elem.click()
            sl_num = i
            i += 1

            while True:
                try:
                    tl_elem = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.XPATH,
                            "//div[@id = 'ctl00_MainContent_tvBrowseNodes']"
                            f"/div[@id = 'ctl00_MainContent_tvBrowseNodesn{fl_num}Nodes']"
                            f"/div[@id = 'ctl00_MainContent_tvBrowseNodesn{sl_num}Nodes']"
                            f"//a[@id = 'ctl00_MainContent_tvBrowseNodest{i}']"
                        ))
                    )
                except TimeoutException:
                    print('y3')
                    break  # no more third-level elements

                data_ids.append(tl_elem.get_attribute('id'))
                print(i, end=' ', flush=True)

                # LOGIC TO DOWNLOAD DATASET:
                tl_name = tl_elem.text
                dataset_name = '__'.join([fl_name, sl_name, tl_name])
                driver = get_info_from_dataset(driver, tl_elem, dataset_name, save_dir)

                i += 2  # unsure why this is different to first/second levels 

        driver.quit()

    return data_ids


if __name__ == "__main__":
    SAVE_DIR = os.path.join(os.getcwd(), "infoshare_downloads")
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    data_ids = navigate_mainpage(SAVE_DIR)
    
    print("Number of datasets:", len(data_ids))
