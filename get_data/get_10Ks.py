import requests as req

SIC = 6021


def get_req(url):
    r = req.get(url)
    if r.ok:
        return r.text
    else:
        print(f'Error getting {url}: {r.status_code}')
        return None


def post_req(url, data):
    r = req.post(url, data=data)
    if r.ok:
        return r.text
    else:
        print(f'Error posting {url}: {r.status_code}')
        return None


def get_company_cik_name(text):
    pass


def more_companies(text):
    pass


def next_page(text):
    pass


def get_list_of_companies(SIC):
    url_list_of_companies = 'https://www.sec.gov/cgi-bin/browse-edgar?'
    'company=&match=&filenum=&State=&Country=&'
    f'SIC={SIC}&myowner=exclude&action=getcompany'

    text = get_req(url_list_of_companies)
    if text is None:
        return None

    company_data = get_company_cik_name(text)

    while more_companies(text):

        text = next_page(text)
        company_data.extend(get_company_cik_name(text))

    return company_data


company_data = get_list_of_companies(SIC)

# for block in resp.iter_content(1024):
#     f.write(block)
