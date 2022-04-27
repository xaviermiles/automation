import json

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from utils import get_driver


def parse_subtheme(d, theme_xpath, subtheme_num):
    subtheme_xpath = f"{theme_xpath}/ul/li[{subtheme_num}]"
    try:
        subtheme_name = d.find_element(By.XPATH, f"{subtheme_xpath}/span").text
    except NoSuchElementException:
        print("skipped") # this happens when datasets are directly underneath theme
        return None
    d.find_element(By.XPATH, subtheme_xpath).click()

    # Seem like: <a> with class "ds" is datasets, class "mi" is infomation sidebar
    datasets = d.find_elements(By.XPATH, f"{subtheme_xpath}/ul/li/a[@class = 'ds']")
    dataset_names = [d.text for d in datasets]

    return subtheme_name, dataset_names


def parse_theme(d, treeview_xpath, theme_num):
    theme_xpath = f"{treeview_xpath}/li[{theme_num}]"
    theme_name = d.find_element(By.XPATH, f"{theme_xpath}/span").text
    print(theme_name)
    
    d.find_element(By.XPATH, theme_xpath).click()
    
    num_subthemes = len(d.find_elements(By.XPATH, f"{theme_xpath}/ul/li"))
    subthemes = [parse_subtheme(d, theme_xpath, i) for i in range(1, num_subthemes + 1)]
    subthemes_unpacked = {s[0]: s[1] for s in subthemes if s is not None}
    
    return theme_name, subthemes_unpacked


def parse_nzdotstat():
    d = get_driver()
    d.get("https://nzdotstat.stats.govt.nz/")

    treeview_xpath = "//div[@id = 'browsethemes']/ul"

    num_themes = len(d.find_elements(By.XPATH, f"{treeview_xpath}/li"))
    themes = [parse_theme(d, treeview_xpath, i) for i in range(1, num_themes + 1)]
    themes_unpacked = {t[0]: t[1] for t in themes}

    with open("data/nzdotstat_summary.json", "w") as f:
        json.dump(themes_unpacked, f, indent = 2)

    d.quit()


if __name__ == "__main__":
    parse_nzdotstat()
