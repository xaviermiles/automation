"""
Simplified version of `../check_covid_portal.py` with local imports removed
"""
import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_driver(save_dir, download_filetypes):
    # Given choice of browser, copy in corresponding code from `../utils.py`
    # (or write new stuff if not Firefox/Chrome)
    pass


def downloads_wait(filepaths, timeout, retry_interval=0.5):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        for f in filepaths.copy():
            if os.path.exists(f):
                filepaths.remove(f)
        if len(filepaths) == 0:
            dl_wait = False
        
        sleep(retry_interval)
        seconds += retry_interval
    return not dl_wait


def attempt_covid_portal_download(driver, download_dir):
    DOWNLOAD_WAIT = 5 * 60  # five minutes

    # Download full dataset - long wait since page will still be loading
    orange_download_btn = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "download_data-show"))
    )
    orange_download_btn.click()
    sleep(10)  # give it some time to catch up - how to make implicit?
    actual_download_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "download_data-downloadData"))
    )
    # Use js to click button (so it can get around the survey popup)
    driver.execute_script("arguments[0].click();", actual_download_btn)

    download_fpath = os.path.join(download_dir, "covid_19_data_portal.xlsx")
    if os.path.exists(download_fpath):
        os.remove(download_fpath)  # clear previous downloads
    download_successful = downloads_wait({download_fpath}, DOWNLOAD_WAIT)

    driver.quit()
    return download_successful


def check_covid_portal(url, download_dir):
    msg = None

    driver = get_driver(download_dir, "csv")
    driver.get(url)
    try:
        download_successful = attempt_covid_portal_download(driver,
                                                            download_dir)
    except Exception as e:
        driver.quit()
        download_successful = True # not really, but don't want msg overwritten
        msg = """
        Automated checking of COVID_19 Portal failed (exception)<br>
        <br>
        Exception:<br>
        {exception}<br>
        <br>
        ~ Automation
        """.format(exception=repr(e))
        subject = "COVID-19 Portal Checking BROKEN"

    if not download_successful:
        msg = """
        Automated checking of COVID-19 Portal failed (download unsuccessful)<br>
        <br>
        Please check live site manually: {url}<br>
        <br>
        ~ Automation
        """.format(url=url)
        subject = "COVID-19 Portal NOT WORKING?"

    # if msg:
    #     outlook.email_alert(msg, subject=subject)
    
    # Not sure how alerts work in Azure, but I was previously using O365 package
    # (Office 365 API) to send email alert
    print(msg)
    print(subject)


if __name__ == "__main__":
    url = "https://statisticsnz.shinyapps.io/covid_19_dashboard/"
    download_dir = os.path.join(os.getcwd(), "data")

    check_covid_portal(url, download_dir)
