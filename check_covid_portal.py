import os
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import utils
from data_releases import outlook


def get_live_site(driver):
    driver.get("https://www.stats.govt.nz/experimental/covid-19-data-portal")
    return driver


def get_staging_page(driver):
    driver.get("https://statisticsnz.shinyapps.io/covid_19_dashboard_staging/")
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


def attempt_covid_portal_download(driver, live_site, download_dir):
    if live_site:
        driver = get_live_site(driver)
    else:
        driver = get_staging_page(driver)
    sleep(10) # explicit wait since page load always takes time

    # Download full dataset
    orange_download_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "download data-show"))
    )
    orange_download_btn.click()
    actual_download_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "download_data-downloadData"))
    )
    acutal_download_btn.click()
    # Wait 2min 30sec for download
    download_fpath = os.path.join(download_dir, "covid_19_portal_data.xlsx")
    download_successful = downloads_wait(download_fpath, 150)

    sleep(10)
    driver.quit()
    return True


def check_covid_portal(live_site, download_dir):
    driver = utils.get_driver(download_dir, "csv")
    download_successful = attempt_covid_portal_download(driver, live_site,
                                                        download_dir)
    # try:
    #     download_successful = attempt_covid_portal_download(driver, live_site,
    #                                                         download_dir)
    # except Exception as e:
    #     print("EXCEPTION")
    #     print(e)
    #     driver.quit()
    #     return
    if not download_successful:
        msg = """
        Automated checking of COVID-19 Portal failed (download unsuccessful).

        Please check live site manually:
        https://www.stats.govt.nz/experimental/covid-19-data-

        ~ Automation
        """
        outlook.email_alert(msg, subject="COVID-19 Portal Down?")


if __name__ == "__main__":
    live_site = False
    download_dir = os.path.join(os.getcwd(), "data")

    check_covid_portal(live_site, download_dir)
