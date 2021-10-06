"""
There is three levels in Infoshare - category, group, dataset
This script navigates all 3 levels to the next dataset and recursively breaks
back up to the next level (and looks for next element), recording the dataset
details. (It is acting like a depth-first search.)
Then it uses the get_infoshare_dataset function (from infoshare/download.py) to
download the datasets.

TODO:
    - custom functions for special-case datasets
"""
import os
import csv

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import utils
from infoshare import download


def get_num_fl_folders(save_dir):
    driver = utils.get_driver(save_dir, ['text/csv'])
    driver.get("http://infoshare.stats.govt.nz/")
    num_fl_folders = len(driver.find_elements_by_xpath(
        "//div[@id = 'ctl00_MainContent_tvBrowseNodes']"
        "//td[@style]"
        "/a[starts-with(@id, 'ctl00_MainContent_tvBrowseNodest')]"
    ))
    driver.quit()
    return num_fl_folders


def find_all_datasets(save_dir):
    """
    An new browser/driver is required for each first-level folder since
    Infoshare becomes slower (?) once there is a large number of second-level
    folders open.
    
    The strings in fake_sl_names refer to datasets which are included in a 
    first-level folder, rather than a second-level folder. Logic to handle these
    is not yet implemented, but will probably need to be custom for each one.
    """
    fake_sl_names = [
        "Harmonised Trade - Exports",
        "Harmonised Trade - Imports",
        "Harmonised Trade - Re-exports",
        ("International Travel and Migration: To access tables, please "
         "refer to this subject under the Tourism category.")
    ]
    print("--- Finding all datasets ---", end='', flush=True)
    num_fl_folders = get_num_fl_folders(save_dir)
    print(f" from {num_fl_folders} categories ---")
    datasets = []
    for fl_num in range(num_fl_folders):
        driver = utils.get_driver(save_dir, ['text/csv'])
        driver.get("http://infoshare.stats.govt.nz/")
        try:
            fl_elem = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.ID,
                    f"ctl00_MainContent_tvBrowseNodest{fl_num}"
                ))
            )
        except TimeoutException:
            print("Page loading too slowly.")
            break
        fl_name = fl_elem.text
        print(fl_num, fl_name)
        i = fl_num + 1
        fl_elem.click()

        while True:
            try:
                sl_elem = WebDriverWait(driver, 4).until(
                    EC.element_to_be_clickable((By.XPATH,
                        f"//div[@id = 'ctl00_MainContent_tvBrowseNodesn{fl_num}Nodes']"
                        f"//a[@id = 'ctl00_MainContent_tvBrowseNodest{i}']"
                    ))
                )
            except TimeoutException:
                print('y2')
                break  # no more second-level elements
            sl_name = sl_elem.text
            print(f"  > {sl_name}:", end=' ', flush=True)
            sl_num = i
            if sl_name in fake_sl_names:
                i += 2  # unsure why this is different to normal
                print("skipping")  # not yet implemented
                continue
            else:
                i += 1
            sl_elem.click()

            while True:
                try:
                    tl_elem = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.XPATH,
                            f"//div[@id = 'ctl00_MainContent_tvBrowseNodesn{fl_num}Nodes']"
                            f"/div[@id = 'ctl00_MainContent_tvBrowseNodesn{sl_num}Nodes']"
                            f"//a[@id = 'ctl00_MainContent_tvBrowseNodest{i}']"
                        ))
                    )
                except TimeoutException:
                    print('y3')
                    break  # no more third-level elements
                tl_name = tl_elem.text
                print(i, end=' ', flush=True)
                i += 2  # unsure why this is different to first/second levels
                datasets.append((fl_name, sl_name, tl_name))
                
        driver.quit()
    
    print(f"--- Found all {len(datasets)} datasets ---\n")
    return datasets


def scrape_all_infoshare(save_dir):
    dataset_refs = find_all_datasets(save_dir)
    
    with open(f"{save_dir}/00_datasets_catalogue.csv", 'w') as f:
        csv_out = csv.writer(f)
        csv_out.writerow(('category','group','dataset'))
        csv_out.writerows(dataset_refs)
    
    for dataset_ref in dataset_refs:
        download.get_infoshare_dataset(
            dataset_ref=dataset_ref,
            title_to_options='ALL',
            dataset_name='__'.join(dataset_ref).replace('/', ' '),
            save_dir=save_dir,
            show_status_flags=True,
            get_metadata=True
        )
    print("\nSCRAPED ALL")


if __name__ == "__main__":
    save_dir = os.path.join(os.getcwd(), 'data', 'all_infoshare')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    scrape_all_infoshare(save_dir)
