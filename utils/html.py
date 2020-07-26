import re
from bs4 import NavigableString

regex_html_tag = re.compile(r'<[^>]+>')
regex_html_tag_or_data = re.compile(r'(<[^]]+>)|([^<]+)')
regex_tag_name = re.compile(r'<([^/ >]+?)\s[^>]*>', re.MULTILINE)
regex_tag_attrs = re.compile(r'(\w+=\"[^\"]+\"\s*)+?', re.MULTILINE)
regex_number = re.compile(r'^\$?(\(?[\d\,]*?\.?[\d]*\)?)\%?$', re.MULTILINE)
regex_multiple_semicolons = re.compile(r'\;{2,}', re.MULTILINE)
regex_subattr_no_value = re.compile(r'\;[^\;\:]+\;', re.MULTILINE)

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


def remove_extra_characters(attr_values):

    attr_values = regex_subattr_no_value.sub(';', attr_values)
    attr_values = attr_values.strip()
    attr_values = regex_multiple_semicolons.sub(';', attr_values)
    if attr_values[-1] == ';':
        attr_values = attr_values[:-1]
    if attr_values[0] == ';':
        attr_values = attr_values[1:]

    return attr_values


def get_attr_subnames_and_values(attr_name, attr_values):
    attr_values = remove_extra_characters(attr_values)
    attr_subnames_and_values_list = \
        [tuple(part.split(':'))
            for part in attr_values.split(';')]
    attr_subnames_and_values_list = \
        list(filter(lambda x: True if len(x) == 2 else False,
                    attr_subnames_and_values_list))
    try:
        attr_subnames_and_values_list = \
            list(map(lambda x: (x[0], x[1]),
                     attr_subnames_and_values_list))
    except (TypeError, IndexError) as e:
        print(f'attr_name: {attr_name}')
        print(f'attr_values: {attr_values}')
        print(f'attr_subnames_and_values_list: '
              f'{attr_subnames_and_values_list}')
        raise e
    return attr_subnames_and_values_list


def get_attr_names_values(tag):
    attr_names_values = []
    if isinstance(tag, NavigableString):
        return attr_names_values
    for attr_name, attr_values in tag.attrs.items():
        try:
            if isinstance(attr_values, list):
                attr_values = ' '.join(attr_values)
            attr_values = attr_values.strip()
        except AttributeError as e:
            print(f'attr_name: {attr_name}')
            print(f'attr_values: {attr_values}\n')
            raise e
        if ':' in attr_values:
            attr_subnames_and_values_list = \
                get_attr_subnames_and_values(attr_name, attr_values)

            attr_names_values.append(attr_name)
            for sub_name, sub_value in attr_subnames_and_values_list:
                attr_names_values.append(sub_name)
                attr_names_values.append(sub_value)
        else:
            attr_names_values.append(attr_name)
            attr_names_values.append(attr_values)
    return attr_names_values


def get_start_tag_string(tag):

    full_tag_str = str(tag)
    end_tag_idx = full_tag_str.find('>')
    if end_tag_idx == -1:
        raise IndexError('Could not find end of tag')

    return full_tag_str[:end_tag_idx+1]


def get_number(text):
    match = regex_number.fullmatch(text)

    # If the whole match is not just a period, $, or comma,
    # then we have a valid number.
    if match is not None \
       and match.group(0) not in ['.', '$', ',', '(', ')']:

        result = match.group(1)
        result = result.replace(',', '') \
            .replace('$', '') \
            .replace('%', '')
        if '(' in result or ')' in result:
            result = result.replace('(', '-') \
                .replace(')', '')
        if len(result) == 0:
            return False
        return result
    else:
        return False
