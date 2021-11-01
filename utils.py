import os
import json
from time import sleep

import jsonschema
import yaml
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


def read_config(rel_fpath='config.yaml'):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    config_fpath = os.path.join(this_dir, rel_fpath)
    if not os.path.exists(config_fpath):
        raise FileNotFoundError("Please create 'config.yaml' file")
    with open(config_fpath) as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)
    
    # TODO: Could this checking be made into yamlschema?
    # https://stackoverflow.com/questions/3262569/validating-a-yaml-document-in-python
    # https://asdf-standard.readthedocs.io/en/latest/schemas/yaml_schema.html
    schema_fpath = os.path.join(this_dir, 'config_schema.json')
    with open(schema_fpath) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(config, schema)
    except jsonschema.ValidationError as e:
        # prints a lot of output by default
        raise jsonschema.ValidationError(e.message)
    
    return config


def get_driver(save_dir=None, download_filetypes=None):
    """
    save_dir should be absolute (not relative) filepath
    """
    browser_to_use = read_config()['webdriver']['browser_to_use']
    if browser_to_use == 'firefox':
        return get_firefox_driver(save_dir, download_filetypes)
    elif browser_to_use == 'chrome':
        return get_chrome_driver(save_dir)


def get_firefox_driver(save_dir=None, download_filetypes=None):
    """
    Get Selenium-powered Firefox instance
    """
    driver_kwargs = {}
    
    exe_path = read_config()['webdriver'].get('firefox_exe_path')
    if exe_path:
        driver_kwargs['executable_path'] = exe_path
    
    opts = webdriver.FirefoxOptions()
    opts.add_argument("--headless")
    driver_kwargs['options'] = opts
    
    if save_dir and download_filetypes:
        # Profile preferences necessary for download-on-click files
        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting",
                               False)
        profile.set_preference("browser.download.dir", save_dir)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               ','.join(download_filetypes))
        driver_kwargs['firefox_profile'] = profile
    elif save_dir or download_filetypes:
        raise ValueError("Please provide both save_dir and download_filetypes "
                         "(not just one)")
    
    this_fpath = os.path.abspath(__file__)
    gecko_fpath = os.path.join(os.path.dirname(this_fpath), 'geckodriver.log')
    driver_kwargs['log_path'] = gecko_fpath
    
    driver = webdriver.Firefox(**driver_kwargs)
    return driver


def get_chrome_driver(save_dir=None):
    """
    Get Selenium-powered Chrome instance
    """
    driver_kwargs = {}
    
    exe_path = read_config()['webdriver'].get('chrome_exe_path')
    if exe_path:
        driver_kwargs['executable_path'] = exe_path
        
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--start-maximized")
    if save_dir:
        opts.add_experimental_option("prefs", {
            "download.default_directory": save_dir,
            "download.prompt_for_download": False
        })
    driver_kwargs['options'] = opts
    
    try:
        driver = webdriver.Chrome(**driver_kwargs)
    except WebDriverException:
        raise WebDriverException("Check chrome executable path is correctly specified")
    except OSError:
        raise OSError("Check chrome executable path is correctly specified")
    
    return driver


def downloads_wait(filepaths, timeout, retry_interval=0.5):
    """
    Wait for downloads to finish with a specified timeout.
    
    Return boolean to indicate whether all downloads were completed.

    Args
    ----
    filepaths : set[str]
        The filepaths where the files will be downloaded.
    timeout : int
        How many seconds to wait until timing out.
    retry_interval : float
        How many seconds to wait between retries.

    """
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
