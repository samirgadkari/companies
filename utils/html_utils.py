import re
import copy
from bs4 import BeautifulSoup

regex_html_tag = re.compile(r'<[^>]+>')

def replace_html_tags(text):
    return regex_html_tag.sub(' ', text)

class Soup():
    def __init__(self, data):
        self.data = data
        self.soup = BeautifulSoup(data, 'html.parser')

    def tags(self):
        return self.soup.find_all(True)

    def text(self):
        return self.soup.get_text()

    def keep_only_row_col_spans(self):
        tags = self.soup.find_all(True)
        for tag in tags:
            attrs = [attr for attr in tag.attrs.keys()]
            for attr in attrs:
                if attr not in ['rowspan', 'colspan']:
                    del tag[attr]

    def remove_span_tags(self):
        spans = self.soup('span')
        for span in spans:
            span.decompose()

