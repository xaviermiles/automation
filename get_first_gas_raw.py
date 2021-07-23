import os
import re
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select


def get_driver():
    opts = webdriver.FirefoxOptions()
    opts.add_argument("--headless")
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", OUTPUT_FOLDER)
    download_filetypes = ("application/octet-stream"
                          ",application/download; charset=utf-8")
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                           download_filetypes)
    driver = webdriver.Firefox(options=opts, firefox_profile=profile)
    return driver


def by_largest_users():
    print("Starting: by_largest_users")
    driver = get_driver()
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
        raise NotImplementedError("Section with Maui SQMQ reports not found.")
    
    latest_report = driver.find_elements_by_xpath(
        f"//table[@id = 'DocumentCategoryDataList__ctl{section_num}_DocumentDataList']"
        "//a[contains(@id, 'DocumentLinkButton')]"
    )[-1]
    default_fpath = os.path.join(OUTPUT_FOLDER, f"{latest_report.text}.xlsx")
    latest_report.click()
    altered_fpath = os.path.join(OUTPUT_FOLDER, "Maui SQMQ Report.xlsx")
    os.rename(default_fpath, altered_fpath)  # overwrites previous copy
    
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
        'BAL08201': ['8201'],
        'BAL09626': ['9626'],
        'GLB03401': ['3401', '3402'],
        'KIN04310': ['4301', '4302'],
        'MSD01801': ['1801', '1803'],
        'STR00521': ['521', '522'],
        'TCC00201': ['201', '202'],
        'TRC02003': ['2003', '2004']
    }
    
    driver = get_driver()
    driver.get(
        "https://www.oatis.co.nz/Ngc.Oatis.UI.Web.Internet/Common/"
        "OatisLogin.aspx"
    )
    # 1. Go to 'First gas'
    driver.find_element_by_id('NGCIX').click()
    # 2. Select 'Daily Delivery Report (DDR) Details Page'
    driver.find_element_by_id('DDRReportLinkButton').click()
    # 3. Select the latest month
    month_dropdown = Select(driver.find_element_by_id('MonthDropDown'))
    dates = [datetime.strptime(l.text, "%b %Y") for l in month_dropdown.options
             if l.text]
    latest_date = max(dates)
    latest_date_str = datetime.strftime(latest_date, '%b %Y')
    month_dropdown.select_by_visible_text(latest_date_str)
    # 4. Select welded points/IDs for the latest month
    for welded_pt in welded_pt_to_meters.keys():
        print(f"{welded_pt}: ", end='', flush=True)
        for meter in welded_pt_to_meters[welded_pt]:
            print(f"{meter}, ", end='', flush=True)
            try:
                welded_pt_dropdown = Select(
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.ID, 'WeldedPointCodes'))
                    )
                )
                welded_pt_dropdown.select_by_visible_text(welded_pt)
                meter_dropdown = Select(
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.ID, 'MeterGroupCodes'))
                    )
                )
                meter_dropdown.select_by_visible_text(meter)
            except TimeoutException:
                raise NotImplementedError("Page has changed or is very slow to load")
            # Download the data for each meter, replacing the previous versions
            download_fpath = os.path.join(OUTPUT_FOLDER, f"DDR{meter}.csv")
            if os.path.exists(download_fpath):
                os.remove(download_fpath)
            driver.find_element_by_id('DownloadButton').click()
        print()
    
    print("Finished: selected_major_users\n")
    driver.quit()
    

if __name__ == "__main__":
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'covid_portal_raw', 'First Gas')
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    by_largest_users()
    by_selected_major_users()
