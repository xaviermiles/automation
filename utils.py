import os

import yaml
from selenium import webdriver


def read_config():
    this_fpath = os.path.abspath(__file__)
    config_fpath = os.path.join(os.path.dirname(this_fpath), 'config.yaml')
    with open(config_fpath) as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)
    
    REQ_FIELDS = ['o365', 'alert_email_addresses']
    if any(field not in config.keys() for field in REQ_FIELDS):
        raise NotImplementedError("config doesn't include all necessary fields")
    # TODO: Could this checking be improved?
    # https://stackoverflow.com/questions/3262569/validating-a-yaml-document-in-python
    # https://asdf-standard.readthedocs.io/en/latest/schemas/yaml_schema.html
    
    return config


def get_firefox_driver(save_dir=None, download_filetypes=None):
    """
    save_dir should be full/absolute (not relative) filepath
    """
    driver_kwargs = {}
    
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
