"""Scrape First Gas datasets for COVID-19 data portal"""
import os
import shutil
import re
from datetime import datetime, timedelta

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

import utils
from infoshare import download


def by_largest_users():
    print("Starting: by_largest_users")
    driver = utils.get_driver(SAVE_DIR, ['application/octet-stream'])
    driver.get(
        "https://www.oatis.co.nz/Ngc.Oatis.UI.Web.Internet/Common/"
        "OatisLogin.aspx"
    )
    # 1. Click 'Maui'
    driver.find_element_by_id('MauiIX').click()
    # 2. Go to 'Publications'
    driver.find_element_by_id('HeaderMenuControl1_LinkPublications').click()
    # 3. Download latest report in 'Daily Metered and Scheduled Quantity Report',
    #    replacing the previous version
    report_sections = driver.find_elements_by_xpath(
        "//table[@id = 'DocumentCategoryDataList']"
        "//span[contains(@id, 'DocumentCategoryLabel')]"
    )
    section_num = None
    for section in report_sections:
        if section.text == 'Daily Metered and Scheduled Quantity Report':
            section_id = section.get_attribute('id')
            section_num = re.match(
                r'DocumentCategoryDataList__ctl(\d+)_DocumentCategoryLabel',
                section_id
            ).group(1)
            break
    if section_num is None:
        raise ValueError("Section with Maui SQMQ reports not found.")

    latest_report = driver.find_elements_by_xpath(
        f"//table[@id = 'DocumentCategoryDataList__ctl{section_num}_DocumentDataList']"
        "//a[contains(@id, 'DocumentLinkButton')]"
    )[-1]
    default_fpath = os.path.join(SAVE_DIR, f"{latest_report.text}.xlsx")
    latest_report.click()
    altered_fpath = os.path.join(SAVE_DIR, "Maui SQMQ Report.xlsx")
    download_successful = utils.downloads_wait({default_fpath}, 5)
    if not download_successful:
        raise NotImplementedError("Download of Maui report timed out")
    # overwrites previous copy:
    if os.path.exists(altered_fpath):
        os.remove(altered_fpath)
    os.rename(default_fpath, altered_fpath)

    print("Finished: by_largest_users\n")
    driver.quit()


def by_selected_major_users():
    print("Starting: by_selected_major_users")
    welded_pt_to_meters = {
        'EGC30701': ['30701', '30703'],
        'KUR33601': ['33601'],
        'LCF20010': ['20001'],
        'LCF20011': ['20021', '20022'],
        'MRV16301': ['16301'],
        'MUT19001': ['19001'],
        'PHT04902': ['4921'],
        'TAC31001': ['9931003'],
        'TIR33501': ['33501'],
        # 'BAL08201': ['8201'],  # no longer updated?
        'BAL09626': ['9626'],
        'GLB03401': ['3401', '3402'],
        'KIN04310': ['4301', '4302'],
        'MSD01801': ['1801', '1803'],
        'STR00521': ['521', '522'],
        'TCC00201': ['201', '202'],
        'TRC02003': ['2003', '2004']
    }

    driver = utils.get_driver(SAVE_DIR,
                              ['application/download; charset=utf-8'])
    driver.get(
        "https://www.oatis.co.nz/Ngc.Oatis.UI.Web.Internet/Common/"
        "OatisLogin.aspx"
    )
    # 1. Go to 'First gas'
    driver.find_element_by_id('NGCIX').click()
    # 2. Select 'Daily Delivery Report (DDR) Details Page'
    driver.find_element_by_id('DDRReportLinkButton').click()
    # 3. Select the previous/second-most-recent month
    month_dropdown = Select(driver.find_element_by_id('MonthDropDown'))
    yesterday = datetime.today() - timedelta(days=1)
    yesterday_month_str = datetime.strftime(yesterday, "%b %Y")
    try:
        month_dropdown.select_by_visible_text(yesterday_month_str)
    except NoSuchElementException:
        raise NoSuchElementException(
            f"Previous month ({yesterday_month_str}) not an option."
        )
    # 3.9 Create "Previous" folder if necessary
    previous_dir = os.path.join(SAVE_DIR, "Previous")
    if not os.path.exists(previous_dir):
        os.makedirs(previous_dir)
    # 4. Select welded points/IDs for the latest month and download
    for welded_pt in welded_pt_to_meters.keys():
        print(f"{welded_pt}: ", end='', flush=True)
        for meter in welded_pt_to_meters[welded_pt]:
            print(f"{meter}, ", end='', flush=True)
            _ = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//select[@id = 'WeldedPointCodes']/option"
                                                )),
                message="Welded pts dropdown not found."
            )
            welded_pt_dropdown = Select(
                driver.find_element_by_id('WeldedPointCodes')
            )
            welded_pt_dropdown.select_by_visible_text(welded_pt)

            _ = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//select[@id = 'MeterGroupCodes']/option"
                                                )),
                message="Meter dropdown not found."
            )
            meter_dropdown = Select(
                driver.find_element_by_id('MeterGroupCodes')
            )
            meter_dropdown.select_by_visible_text(meter)
            # Download the data for each meter, moving the previous versions
            # out of the way
            download_fpath = os.path.join(SAVE_DIR, f"DDR{meter}.csv")
            if os.path.exists(download_fpath):
                shutil.move(download_fpath, previous_dir)
            driver.find_element_by_id('DownloadButton').click()
        print()

    print("Finished: selected_major_users\n")
    driver.quit()


if __name__ == "__main__":
    SAVE_DIR = os.path.join(os.getcwd(), 'data', 'covid_portal_raw')
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    by_largest_users()
    by_selected_major_users()
