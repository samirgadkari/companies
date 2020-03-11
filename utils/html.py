import re
import copy
from bs4 import BeautifulSoup

regex_html_tag = re.compile(r'<[^>]+>')
regex_html_tag_or_data = re.compile(r'(<[^]]+>)|([^<]+)')

def replace_html_tags(text):
    return regex_html_tag.sub(' ', text)

def next_tag_or_data(data):
    item = regex_html_tag_or_data.search(data)
    return item, len(item)
