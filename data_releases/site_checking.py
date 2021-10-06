import re
import requests

import utils


def check_date_str(url, text_template, date_str, xpath=None, css=None):
    """Checks if a click-to-download dataset is updated using regex searching.
    
    url (str) - URL where dataset is downloadable from
    text_template (str) - regex expression for text of relevant HTML element
        This should contain '<date_str>' substring where the most recent date
        will be specified
    date_str (str) - date-text to check for
    xpath (str) OR css (str) - only one can be used; this should be able to
        uniquely identify the relevant HTML element
    
    Return (updated, info) where:
      - "updated" is True if the date_str is found, False if not, or None if an
        error was thrown
      - "info" will describe error thrown (updated=None) or element's text
        if no errors thrown (updated=True or updated=False)
    """
    if text_template.count('<date_str>') != 1:
        return None, "text_template must contain exactly one '<date_str>' substring"
    if (xpath and css) or (xpath is None and css is None):
        return None, "Exactly one of xpath or css must be specified"
    
    driver = utils.get_driver()
    driver.get(url)
    try:
        if xpath:
            elem = driver.find_element_by_xpath(xpath)
        else:
            elem = driver.find_element_by_css(css)
    except NoSuchElementException:
        search_type = "xpath" if xpath else "css"
        return None, f"Could not find HTML element according to {search_type}"
    
    # Check text_template is valid (NB: does not check date formatting)
    latest_date_re = re.search(text_template.replace('<date_str>', '.*'),
                               elem.text)
    if not latest_date_re:
        return None, "text_template is not valid for the HTML element"
    
    # Check whether date in HTML element's text matches date_str
    if re.search(text_template.replace('<date_str>', date_str), elem.text):
        return True, elem.text
    else:
        return False, elem.text
