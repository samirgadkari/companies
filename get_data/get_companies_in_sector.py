import re
import sys
import json
import html
import selenium
import functools
import operator
from .selenium_utils import *
from decouple import config
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


SIC_codes = {
    'banks': 6021, # SIC code for National Commercial Banks
}

regex_replace_chars = re.compile(r'\s|\/|\\')


def replace_chars(match):
    return '_'


def get_url(sector):
    return f'https://www.sec.gov/cgi-bin/browse-edgar?' \
        f'company=&match=&filenum=&State=&Country=&' \
        f'SIC={SIC_codes[sector]}&myowner=exclude&action=getcompany'


def process_page(browser):
    # Unfortunately, the page does not have id/class tags associated
    # with anything below the table element.
    # We can find elements by tag name, and keep only those that we need.
    links = browser.find_elements_by_tag_name('a')
    company_links = []
    for link in links:
        href = link.get_attribute('href')
        if 'CIK=' in href:
            company_links.append(href)

    # XPATH search is a little slower, but there is nothing in the
    # company name <td> element that is unique to company names,
    # so we don't have a choice here.
    company_names_xpath = \
        '//table[@class = "tableFile2"]/tbody/tr/td[2]'
    names = browser.find_elements_by_xpath(company_names_xpath)
    company_names = []
    for name in names:
        company_names.append(name.text)

    # Extract CIK numbers from the company links
    parts = [link.split('&') for link in company_links]  # Gives list of lists
    parts = functools.reduce(operator.concat, parts)     # Flatten list of lists
    CIKs = [part.split('=')[1] for part in parts if 'CIK=' in part]

    return zip(CIKs, company_names, company_links)


def all_company_pages(browser, url):

    companies = []
    ctr = 0
    while url is not None:
        print(f'Getting: {url}')
        browser.get(url)
        companies.extend(process_page(browser))

        button_xpath = \
            '//input[contains(@type, "button") and contains(@value,"Next 40")]'
        buttons = browser.find_elements_by_xpath(button_xpath)
        if len(buttons) == 0:
            break

        for button in buttons:
            res = button.get_attribute('onclick')
            if res is not None:
                on_click = button.get_attribute('onclick')

        if on_click is None:
            url = None
        else:
            after_split = on_click.split("'")
            next_page_link = 'https://www.sec.gov/' + \
                on_click.split("'")[1]
            url = next_page_link

        ctr += 1

    print(f'number of pages: {ctr}')
    print(f'companies: {companies}')
    return companies


def build_output(companies_list):
    CIKs, names, links = zip(*companies_list)
    CIKs = list(CIKs)     # Iterators are done once used, lists aren't.
    names = list(names)

    company_links = []
    for idx, link in enumerate(links):
        pre, post = link.split(f'&CIK={CIKs[idx]}')
        company_links.append(pre + post)

    companies = {}
    for idx, CIK in enumerate(CIKs):
        companies[CIK] = {
            'CIK': CIK,
            'link': company_links[idx],
            'name': regex_replace_chars.sub(replace_chars,
                                            html.unescape(names[idx]))
        }

    return companies


def get_companies():
    banking_companies = \
      all_company_pages(selenium_utils.configure_browser(),
                        get_url('banks'))
    companies = build_output(banking_companies)

    with open(config('DATA_DIR') + '/' + 'banking_companies.json', 'w') as f:
        json_str = json.dumps(companies, indent=4)
        f.write(json_str)

if __name__ == '__main__':
    get_companies()
