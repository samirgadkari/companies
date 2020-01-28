import os
import re
import sys
import json
import urllib
import selenium_utils
from decouple import config
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# Compile regex for faster processing
regex_period_ending = re.compile(r'^\s*CONFORMED PERIOD OF REPORT:\s*(.+)$',
                                 re.MULTILINE)
regex_company_name = re.compile(r'^\s*COMPANY CONFORMED NAME:\s*(.+)$',
                                 re.MULTILINE)
regex_cik = re.compile(r'^\s*CENTRAL INDEX KEY:\s*(.+)$',
                                 re.MULTILINE)


regex_replace_chars = re.compile(r'\/')


def replace_chars(match):
    return '-'


def get_element(regex, data):
    matches = regex.search(data)
    if matches is not None:
        return matches.group(1)
    return None


def get_filing_data(filing, filing_type):
    part_filing = filing[:3000]

    try:
        period_ending_str = get_element(regex_period_ending, part_filing)
        period_ending = datetime.strptime(period_ending_str, '%Y%m%d')
    except (ValueError, TypeError) as e:
        print(f'error raised: e')
        print(f'part_filing: {part_filing}')
        return None

    period_starting = period_ending + \
        relativedelta(years=-1) + \
        relativedelta(days=1)

    # Keep only the YYYY-MM-DD part
    period_starting = str(period_starting)[:10]
    period_ending = str(period_ending)[:10]

    print(f'period_starting: {period_starting}')
    print(f'period_ending: {period_ending}')

    name = get_element(regex_company_name, part_filing)
    CIK = get_element(regex_cik, part_filing)
    filing_data = { 'CIK': CIK,
                    'name': name,
                    'period_starting': period_starting,
                    'period_ending': period_ending,
                    'filing': filing,
                    'filing_type': regex_replace_chars.sub(replace_chars,
                                                           filing_type)}
    print(f"filing_data['period_starting']: {filing_data['period_starting']}")
    print(f"filing_data['period_ending']: {filing_data['period_ending']}")
    print(f"filing_data['filing_type']: {filing_data['filing_type']}")
    return filing_data


def process_page(browser):
    tds = browser.find_elements_by_xpath("//td[contains(text(), '10-K')]")
    if len(tds) == 0:
        return

    filing_types = [e.text for e in tds]

    elements = list(browser.find_elements_by_id('documentsbutton'))
    sec_root = config('SEC_ROOT')

    print(f'starting loop with num elements: {len(elements)}')
    if len(elements) == 0:
        return

    hrefs = [e.get_attribute('href') for e in elements]
    elements_data = zip(elements, filing_types, hrefs)
    company_filings = []
    for (e, filing_type, href) in elements_data:
        if href[:8] != 'https://':
            href = sec_root + '/' + href
        print(f'Getting page at link: {href}')
        browser.get(href)

        file_link_element = browser.find_element_by_xpath(
            "//td[contains(text(), 'Complete submission text file')]"
            "//following-sibling::td//a"
        )
        file_link_element_href = \
            file_link_element.get_attribute('href')
        print(f"file_link_element_href: {file_link_element_href}")
        browser.get(file_link_element_href)
        selenium_utils.browser_sleep(5, 7)

        try:
            filing = browser.page_source
        except WebDriverException as e:
            print(e)
            # Use this only if needed. Urllib does not do such a good job
            # of acting as a browser talking to the server, so
            # if you do this all the time, your access may be blocked.
            filing = urllib.request.urlopen(file_link_element_href).read()

        filing_data = get_filing_data(filing, filing_type)
        if filing_data is None:
            continue

        company_filings.append(filing_data)

        # Sleep for a random interval between the given number of seconds
        selenium_utils.browser_sleep(3, 5)

    return company_filings


def get_10Ks(companies):
    browser = selenium_utils.configure_browser()

    for CIK, company in companies.items():
        d_10k = os.path.join( \
                              config('DATA_DIR'),
                              CIK + '_' + company['name'],
                              '10-k')
        if not os.path.exists(d_10k):
            os.makedirs(d_10k)

        url = f"{company['link']}&CIK={CIK}&type=10-K"
        print(f'Getting url: {url}')
        browser.get(url)
        company_filings = process_page(browser)
        if (company_filings is not None) and \
           (len(company_filings) > 0):
            for filing_data in company_filings:

                name = filing_data['name']
                period_starting = filing_data['period_starting']
                period_ending = filing_data['period_ending']
                filing_type = filing_data['filing_type']
                filename = \
                        os.path.join(d_10k,
                                     period_starting + '_' +
                                     period_ending + '_' +
                                     filing_type)
                with open(filename, 'w') as f:
                    f.write(filing_data['filing'])

        # Sleep for a random interval between the given number of seconds
        selenium_utils.browser_sleep(10, 50)

if __name__ == '__main__':
    with open(os.path.join(
            config('DATA_DIR'), 'banking_companies.json'), 'r') as f:
        companies = json.load(f)

    get_10Ks(companies)
