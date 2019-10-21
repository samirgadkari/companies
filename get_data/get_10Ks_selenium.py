from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options


def configure_browser():
    opts = Options()
    opts.set_headless()
    assert opts.headless

    browser = Firefox(options=opts)
    return browser


def banking_url():
    SIC = 6021  # The SIC code for National Commercial Banks
    banks_url = f'https://www.sec.gov/cgi-bin/browse-edgar?' \
        f'company=&match=&filenum=&State=&Country=&' \
        f'SIC={SIC}&myowner=exclude&action=getcompany'
    # print(f'banks_url: {banks_url}')
    return banks_url


def process_page(browser):
    company_links_xpath = '//table[@class = "tableFile2"]/tbody/tr/td[1]/a'
    # company_links_xpath = '//table[@class = "tableFile2"]'
    company_links = browser.find_elements_by_xpath(company_links_xpath)

    res = []
    for link in company_links:
        res.append(link.get_attribute('href'))
        company_links = res
        # print(f'company_links: {company_links}')

    company_names_xpath = \
        '//table[@class = "tableFile2"]/tbody/tr/td[2]'
    company_names = browser.find_elements_by_xpath(company_names_xpath)
    res = []
    for name in company_names:
        res.append(name.text)
        company_names = res
        # print(f'company_names: {company_names}')

    return zip(company_names, company_links)


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
        print(f'buttons: {buttons}')
        for button in buttons:
            res = button.get_attribute('onclick')
            print(f'res: {res}')
            if res is not None:
                on_click = button.get_attribute('onclick')

        if on_click is None:
            url = None
        else:
            print(f'on_click: {on_click}')
            after_split = on_click.split("'")
            print(f'on_click.split: {after_split}')
            next_page_link = 'https://www.sec.gov/' + \
                on_click.split("'")[1]
            print(f'next_page_link: {next_page_link}')
            url = next_page_link

        ctr += 1
        if ctr > 5:
            break

    print(f'companies: {companies}')
    return companies


# This is the link we have for each company:
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001109525&owner=include&count=40&hidefilings=0
# This is the link we need - the only difference is the &type=10-k is missing after the CIK:
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001109525&type=10-k&dateb=&owner=include&count=40
if __name__ == '__main__':
    banking_companies = all_company_pages(configure_browser(), banking_url())

    with open('banking_companies.txt', 'w') as f:
        for name, link in banking_companies:
            f.write(f'{name}: {link}\n')
