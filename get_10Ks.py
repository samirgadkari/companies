import os
import re
import json
import urllib
import urllib.request
from utils.selenium import configure_browser, browser_sleep
from decouple import config
from selenium.common.exceptions import (WebDriverException,
                                        NoSuchElementException)

# Compile regex for faster processing
regex_period_ending = re.compile(r'^\s*CONFORMED PERIOD OF REPORT:\s*(.+)$',
                                 re.MULTILINE)
regex_company_name = re.compile(r'^\s*COMPANY CONFORMED NAME:\s*(.+)$',
                                re.MULTILINE)
regex_cik = re.compile(r'^\s*CENTRAL INDEX KEY:\s*(.+)$',
                       re.MULTILINE)
regex_filer = re.compile(r'\s*\(Filer\)')

regex_replace_chars = re.compile(r'\/')


def replace_chars(match):
    return '-'


def get_element(regex, data):
    matches = regex.search(data)
    if matches is not None:
        return matches.group(1)
    return None


def get_filing_data(filing, filing_type, browser):

    print(browser.current_url)
    name_element = browser.find_element_by_xpath(
        "//span[@class='companyName']")
    name = name_element.text
    name = name[:name.index('(Filer)')].strip()
    name = regex_replace_chars.sub('_', name, count=2)

    CIK = name_element.find_element_by_xpath("a[1]").text.split()[0]

    period_ending = browser.find_element_by_xpath(
        "//div[contains(text(), 'Period of Report')]"
        "/following-sibling::div").text

    year, month, day = map(int, period_ending.split('-'))
    if month == 12:
        period_starting = str(year) + '-01-01'
    else:
        period_starting = '{}-{:0>2}-{}'.format(str(year - 1),
                                                str(month + 1),
                                                1)

    filing_data = {'CIK': CIK,
                   'name': name,
                   'period_starting': period_starting,
                   'period_ending': period_ending,
                   'filing': filing,
                   'filing_type': regex_replace_chars.sub(replace_chars,
                                                          filing_type)}
    # print(f"filing_data['period_starting']: {filing_data['period_starting']}")
    # print(f"filing_data['period_ending']: {filing_data['period_ending']}")
    # print(f"filing_data['filing_type']: {filing_data['filing_type']}")

    return filing_data


def iXBRL_element_exists(browser):
    try:
        browser.find_element_by_xpath(
            "//table[1]//tbody[1]//tr[2]//td[3]//span[1]")

        # If we came here, iXBRL element exists,
        # so return True
        return True
    except NoSuchElementException:
        return False


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
            "//table[1]//tbody[1]//tr[2]//td[3]//a[1]")

        if iXBRL_element_exists(browser):
            browser_sleep(5, 7)
            # Skip XBRL files as we don't know how to
            # extract data from them yet.
            continue

        file_link_element_href = \
            file_link_element.get_attribute('href')

        if file_link_element_href[-1] == '/':
            print(f'file_link_element_href: {file_link_element_href} is'
                  f'a directory - ignoring')
            browser_sleep(5, 7)
            continue

        browser.get(file_link_element_href)
        browser_sleep(5, 7)

        try:
            filing = browser.page_source
        except WebDriverException as e:
            print('\n\n>>>>>>>>')
            print(f'href: {href}')
            print(e.format_exc())
            print('<<<<<<<<<\n\n')
            ''' Remove this section for now.
            # Use this only if needed. Urllib does not do such a good job
            # of acting as a browser talking to the server, so
            # if you do this all the time, your access may be blocked.
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (X11; Ubuntu; Linux i686;" \
                                    "rv:48.0) Gecko/20100101 Firefox/48.0"
            req = urllib.request.Request(file_link_element_href,
                                         headers=headers)
            filing = urllib.request.urlopen(req).read()
            '''

        # Get the browser back to the page with the list of filings.
        # From this page we want to get the filing information
        # like company name, CIK, start/end date.
        browser.get(href)
        filing_data = get_filing_data(filing, filing_type, browser)
        if filing_data is None:
            # Sleep for a random interval between the given number of seconds
            browser_sleep(5, 7)
            continue

        company_filings.append(filing_data)
        print(f'Got page for {filing_data["name"]} at link: {href}')

        # Sleep for a random interval between the given number of seconds
        browser_sleep(3, 5)

    return company_filings


def get_10Ks():
    with open(os.path.join(
            config('DATA_DIR'), 'banking_companies.json'), 'r') as f:
        companies = json.load(f)

    browser = configure_browser()

    for CIK, company in companies.items():
        d_10k = os.path.join(
            config('DATA_DIR'),
            CIK + '_' + company['name'],
            '10-k')

        # If directory exists, don't get data again.
        dir_exists = os.path.exists(d_10k)
        if dir_exists:
            continue
        # If it does not exist, create directory/sub-directory.
        os.makedirs(d_10k)

        url = f"{company['link']}&CIK={CIK}&type=10-K"
        print(f'Getting url: {url}')
        browser.get(url)
        company_filings = process_page(browser)
        if (company_filings is not None) and \
           (len(company_filings) > 0):
            for filing_data in company_filings:

                # name = filing_data['name']
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
        browser_sleep(10, 50)


if __name__ == '__main__':
    get_10Ks()
