import re

regex_html_tag = re.compile(r'<[^>]+>')

def replace_html_tags(text):
    return regex_html_tag.sub(' ', text)
