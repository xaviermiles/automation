import json
import os
from time import sleep

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import get_driver


def process_dataset(d, subtheme_xpath, dataset_num):
    dataset_path = f"{subtheme_xpath}/ul/li[{dataset_num}]"
    try:
        dataset_elem = WebDriverWait(d, 1).until(
            EC.presence_of_element_located((By.XPATH, f"{dataset_path}/a[@class = 'ds']"))
        )
    except TimeoutException:
        print("skipped dataset")
        return None
    dataset_name = dataset_elem.text
    dataset_elem.click()

    customise_xpath = "//ul[@id = 'menubar-list']/li[1]"
    WebDriverWait(d, 2).until(EC.presence_of_element_located((By.XPATH, customise_xpath)))
    selectors_xpath = f"{customise_xpath}/ul/li[1]/ul/li"
    num_selections = len(d.find_elements(By.XPATH, selectors_xpath))
    print(num_selections)
    for selector_idx in range(1, num_selections + 1):
        customise = d.find_element(By.XPATH, f"{customise_xpath}/a")
        selection = d.find_element(By.XPATH, f"{customise_xpath}/ul/li[1]/a")
        to_be_selected = d.find_element(By.XPATH, f"{customise_xpath}/ul/li[1]/ul/li[{selector_idx}]/a")

        # WebDriverWait(d, 5).until(EC.presence_of_element_located((By.ID, "lbtnViewData")))

        open_customise = ActionChains(d)
        open_customise.move_to_element(customise).move_to_element(selection)
        open_customise.move_to_element(to_be_selected).click(to_be_selected)
        open_customise.perform()
        
        WebDriverWait(d, 5).until(EC.presence_of_element_located((By.ID, "dialog-modal")), message="dialog-modal not found.")

        # Close "Customise selection"
        # close_customise = ActionChains(d)
        close_customise = WebDriverWait(d, 4).until(EC.element_to_be_clickable((By.XPATH, "//a[@class = 'ui-dialog-titlebar-close ui-corner-all']")))
        print(close_customise)
        # close_customise.click()
        sleep(10)
        # close_customise.move_to_element(d.find_element(By.XPATH, "//a[@class = 'ui-dialog-titlebar-close ui-corner-all']"))

    d.quit()
    raise NotImplementedError

    return dataset_name


def parse_subtheme(d, theme_xpath, subtheme_num):
    subtheme_xpath = f"{theme_xpath}/ul/li[{subtheme_num}]"
    try:
        subtheme_name = d.find_element(By.XPATH, f"{subtheme_xpath}/span").text
    except NoSuchElementException:
        print("skipped subtheme") # this happens when datasets are directly underneath theme
        return None
    d.find_element(By.XPATH, subtheme_xpath).click()

    # Seem like: <a> with class "ds" is datasets, class "mi" is infomation sidebar
    num_datasets = len(d.find_elements(By.XPATH, f"{subtheme_xpath}/ul/li"))
    dataset_names = [process_dataset(d, subtheme_xpath, i) for i in range(1, num_datasets + 1)]

    return subtheme_name, dataset_names


def parse_theme(d, treeview_xpath, theme_num):
    theme_xpath = f"{treeview_xpath}/li[{theme_num}]"
    theme_name = d.find_element(By.XPATH, f"{theme_xpath}/span").text
    print(theme_name)
    
    d.find_element(By.XPATH, theme_xpath).click()
    
    num_subthemes = len(d.find_elements(By.XPATH, f"{theme_xpath}/ul/li"))
    subthemes = [parse_subtheme(d, theme_xpath, i) for i in range(1, 2)]#num_subthemes + 1)]
    subthemes_unpacked = {s[0]: s[1] for s in subthemes if s is not None}
    
    return theme_name, subthemes_unpacked


def parse_nzdotstat(save_dir="data"):
    d = get_driver()
    d.get("https://nzdotstat.stats.govt.nz/")

    treeview_xpath = "//div[@id = 'browsethemes']/ul"

    num_themes = len(d.find_elements(By.XPATH, f"{treeview_xpath}/li"))
    themes = [parse_theme(d, treeview_xpath, i) for i in range(1, num_themes + 1)]
    themes_unpacked = {t[0]: t[1] for t in themes}

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    with open(os.path.join(save_dir, "nzdotstat_summary.json"), "w") as f:
        json.dump(themes_unpacked, f, indent = 2)

    d.quit()


if __name__ == "__main__":
    parse_nzdotstat()
