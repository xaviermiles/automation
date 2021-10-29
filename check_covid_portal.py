import os
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import utils
from data_releases import outlook


def login_staging_page(driver):
    main_page = driver.current_window_handle

    driver.find_element_by_xpath("//a[text() = 'Login']").click()
    # Switch to login pop-up window
    for handle in driver.window_handles:
        if handle != main_page:
            login_page = handle
    driver.switch_to.window(login_page)
    # Enter credentials
    cred = utils.read_config()['statisticsnz.shinyapps']
    email_entry = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name = 'email']"))
    )
    email_entry.send_keys(cred['email'])
    driver.find_element_by_xpath("//span[text() = 'Continue']/..").click()
    password_entry = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
    )
    password_entry.send_keys(cred['password'])
    driver.find_element_by_xpath(
        "//span[text() = 'Log In' and ../@type = 'submit']/.."
    ).click()
    # Switch back to original window
    driver.switch_to.window(main_page)

    return driver


def attempt_covid_portal_download(driver, url, download_dir):
    DOWNLOAD_WAIT = 5 * 60  # five minutes
    
    if not live_site:
        driver = login_staging_page(driver)

    # Download full dataset - long wait since page will still be loading
    orange_download_btn = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "download_data-show"))
    )
    orange_download_btn.click()
    actual_download_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "download_data-downloadData"))
    )
    sleep(10)  # give it some time to catch up
    actual_download_btn.click()
    
    download_fpath = os.path.join(download_dir, "covid_19_portal_data.xlsx")
    if os.path.exists(download_fpath):
        os.remove(download_fpath)  # clear previous downloads
    download_successful = utils.downloads_wait({download_fpath}, DOWNLOAD_WAIT)

    driver.quit()
    return download_successful


def check_covid_portal(live_site, download_dir):
    LIVE_SITE_URL = "https://www.stats.govt.nz/experimental/covid-19-data-portal"
    STAGING_URL = "https://statisticsnz.shinyapps.io/covid_19_dashboard_staging/"
    
    driver = utils.get_driver(download_dir, "csv")
    url = LIVE_SITE_URL if live_site else STAGING_URL
    driver.get(url)
    try:
        download_successful = attempt_covid_portal_download(driver,
                                                            live_site,
                                                            download_dir)
    except Exception as e:
        download_successful = True # not really, but don't want msg overwritten
        msg = """
        Automated checking of COVID_19 Portal failed (exception)
        <br><br>
        Exception: {exception}
        <br><br>
        ~ Automation
        """.format(exception=e)
        subject = "COVID-19 Portal Checking BROKEN"
    
    if not download_successful:
        msg = """
        Automated checking of COVID-19 Portal failed (download unsuccessful).
        <br><br>
        Please check live site manually: {url}
        <br><br>
        ~ Automation
        """.format(url=url)
        subject = "COVID-19 Portal NOT WORKING?"
    
    if msg:
        outlook.email_alert(msg, subject=subject)


if __name__ == "__main__":
    live_site = False
    download_dir = os.path.join(os.getcwd(), "data")

    check_covid_portal(live_site, download_dir)
