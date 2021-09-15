"""
Written with latest releases (as of 15 Sep 21) - should give True Positives
"""
from data_releases import site_checking

monthly_info = {
    'mbie_jobs_online': {
        'url': ("https://www.mbie.govt.nz/business-and-employment/"
                "employment-and-skills/labour-market-reports-data-and-analysis/"
                "jobs-online/"),
        'text_template': "Jobs Online Monthly Unadjusted Series from May 2007 to <date_str>",
        'next_date_str': "August 2021",
        'xpath': "//h2[@id='jobs-online-monthly-data-release']/../p[1]/a"
    },
    'tenancy_rental_by_region': {
        'url': ("https://www.tenancy.govt.nz/about-tenancy-services/"
                "data-and-statistics/rental-bond-data/"),
        'text_template': "By region, January 1993 - <date_str>",
        'next_date_str': "July 2021",
        'xpath': "//a[@href='https://www.tenancy.govt.nz/assets/Uploads/Tenancy/Rental-bond-data-/rentalbond-data-regional.csv']"
    },
    'bnz_pmi': {
        'url': ("https://www.businessnz.org.nz/resources/"
                "surveys-and-statistics/pmi"),
        'text_template': "\d{2} <date_str>",
        'next_date_str': "Aug 2021",
        'xpath': "//a[text()='PMI Time Series Data']/../..//li[@class='published-date']"
    },
    'msd_monthly_benefits': {
        'url': ("https://www.msd.govt.nz/about-msd-and-our-work/"
                "publications-resources/statistics/monthly-reporting/"
                "index.html"),
        'text_template': "Data file Monthly Benefits Update - <date_str>",
        'next_date_str': "August 2021",
        'xpath': "//h3[text() = 'Monthly Benefits Update - Data file']/../div[@class='links excel']/a",
    }
}

for indicator, info in monthly_info.items():
    print(indicator)
    updated, error_description = site_checking.check_date_str(
        info['url'],
        info['text_template'],
        info['next_date_str'],
        xpath=info['xpath']
    )
    print(updated, error_description)
    if updated:
        print('yay')
    print()
