import os
import re
import sys
import json
import html
import selenium_utils
from decouple import config
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Compile regex for faster processing
regex_period_ending = re.compile(r'^\s*CONFORMED PERIOD OF REPORT:\s*(.+)$',
                                 re.MULTILINE)
regex_company_name = re.compile(r'^\s*COMPANY CONFORMED NAME:\s*(.+)$',
                                 re.MULTILINE)
regex_cik = re.compile(r'^\s*CENTRAL INDEX KEY:\s*(.+)$',
                                 re.MULTILINE)


def get_element(regex, data):
    matches = regex.search(data)
    if matches is not None:
        print(f'matches.groups: {matches.groups}')
        return matches.group(1)
    return 'None returned from match'


def get_filing_data(filing):
    part_filing = filing[:3000]

    try:
        period_ending_str = get_element(regex_period_ending, part_filing)
        period_ending = datetime.strptime(period_ending_str, '%Y%m%d')
    except ValueError as e:
        print(f'error raised: e')
        print(f'part_filing: {part_filing}')
        sys.exit(0)

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
    return (CIK, { 'CIK': CIK,
             'name': name,
             'period_starting': period_starting,
             'period_ending': period_ending,
             'filing': filing })


def process_page(browser):
    elements = list(browser.find_elements_by_id('documentsbutton'))
    sec_root = config('SEC_ROOT')

    print(f'starting loop with num elements: {len(elements)}')
    if len(elements) == 0:
        return

    hrefs = [e.get_attribute('href') for e in elements]
    elements_hrefs = zip(elements, hrefs)
    print(f'elements_hrefs: {elements_hrefs}')
    company_filings = {}
    for (e, href) in elements_hrefs:
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

        filing = browser.page_source
        CIK, filing_data = get_filing_data(filing)
        company_filings[CIK] = filing_data

        print(f'1 company_filings[CIK]["period_starting"]: '
              f'{company_filings[CIK]["period_starting"]}')

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
        ctr = 0
        if company_filings is not None:
            for CIK, filing_data in company_filings.items():
                print(f'2 filing_data["period_starting"]:'
                      f'{filing_data["period_starting"]}')

                name = html.unescape(filing_data['name'])
                period_starting = str(filing_data['period_starting'])
                period_ending = str(filing_data['period_ending'])
                print(f'config("DATA_DIR"): {config("DATA_DIR")}')
                filename = \
                        os.path.join(d_10k,
                                     period_starting + '_' +
                                     period_ending)
                with open(filename, 'w') as f:
                    # header = f'CIK: {CIK}\n' \
                    #          f'period_starting: {period_starting}\n' \
                    #          f'period_ending: {period_ending}\n' \
                    #          f'name: {name}\n'
                    # f.write(header)
                    f.write(filing_data['filing'])
                    ctr += 1
                if ctr > 1:
                    sys.exit(0)

            break;

        # Sleep for a random interval between the given number of seconds
        selenium_utils.browser_sleep(3, 10)

if __name__ == '__main__':
    with open(os.path.join(
            config('DATA_DIR'), 'banking_companies.json'), 'r') as f:
        companies = json.load(f)

    get_10Ks(companies)
