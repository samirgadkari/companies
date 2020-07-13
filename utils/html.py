import re

regex_html_tag = re.compile(r'<[^>]+>')
regex_html_tag_or_data = re.compile(r'(<[^]]+>)|([^<]+)')

# tag.unwrap(): removes the tag and it's attributes,
# but keeps the text inside.
# tag.decompose(): completely removes a tag and it's contents.
# tag.clear(): removes just the contents (insides) of the tag,
# not the tag itself.
# This table shows the tag name and action to take on the tag.
tag_actions = {
    'a':              'decompose',
    'b':              'untouched',
    'big':            'unwrap',
    'br':             'decompose',
    'body':           'untouched',
    'c':              'decompose',
    'caption':        'decompose',
    'center':         'untouched',
    'dd':             'decompose',
    'dl':             'decompose',
    'dir':            'decompose',
    'div':            'unwrap',
    'dt':             'decompose',
    'em':             'untouched',
    'f1':             'decompose',
    'f2':             'decompose',
    'f3':             'decompose',
    'f4':             'decompose',
    'f5':             'decompose',
    'f6':             'decompose',
    'f7':             'decompose',
    'f8':             'decompose',
    'f9':             'decompose',
    'f10':            'decompose',
    'f11':            'decompose',
    'f1':             'decompose',
    'fn':             'decompose',
    'font':           'unwrap',
    'h1':             'remove_attrs_except[style]',
    'h2':             'remove_attrs_except[style]',
    'h3':             'remove_attrs_except[style]',
    'h4':             'remove_attrs_except[style]',
    'h5':             'remove_attrs_except[style]',
    'h6':             'remove_attrs_except[style]',
    'hr':             'untouched',
    'html':           'untouched',
    'i':              'unwrap',
    'ix:nonfraction': 'unwarp',
    'ix:nonnumeric':  'unwrap',
    'img':            'decompose',
    'li':             'decompose',
    'nobr':           'unwrap',
    None:             'untouched',  # The None name is for the HTML Comment tag
    'p':              'unwrap',
    'page':           'decompose',
    's':              'decompose',
    'small':          'unwrap',
    'span':           'decompose',
    'sup':            'decompose',
    'sub':            'decompose',
    'strong':         'untouched',
    't':              'decompose',
    'table':          'untouched',
    'td':             'remove_attrs_except[rowspan, colspan, style]',
    'th':             'remove_attrs_except[rowspan, colspan, style]',
    'tr':             'remove_attrs_except[rowspan, colspan, style]',
    'u':              'untouched',
    'ul':             'decompose',
}


def replace_html_tags(text):
    return regex_html_tag.sub(' ', text)


def next_tag_or_data(data):
    item = regex_html_tag_or_data.search(data)
    return item, len(item)


def find_descendant_tag_names(descendants):
    descendant_tag_names = set()
    for tag in descendants:
        descendant_tag_names.add(tag.name)

    return descendant_tag_names
