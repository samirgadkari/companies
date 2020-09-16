import re
import string
from bs4 import BeautifulSoup, NavigableString
from ml.number import is_number, YEARS_RANGE

regex_html_tag = re.compile(r'<[^>]+>')
regex_html_tag_or_data = re.compile(r'(<[^]]+>)|([^<]+)')
regex_tag_name = re.compile(r'<([^/ >]+?)\s[^>]*>', re.MULTILINE)
regex_tag_attrs = re.compile(r'(\w+=\"[^\"]+\"\s*)+?', re.MULTILINE)
regex_multiple_semicolons = re.compile(r'\;{2,}', re.MULTILINE)
regex_subattr_no_value = re.compile(r'\;[^\;\:]+\;', re.MULTILINE)
regex_named_or_numeric = re.compile(r'(?:\&.*?\;|\\+x..)',
                                    re.MULTILINE)
regex_whitespace = re.compile(r'\s+', re.MULTILINE)

# tag.unwrap(): removes the tag and it's attributes,
# but keeps the text inside.
# tag.decompose(): completely removes a tag and it's contents.
# tag.clear(): removes just the contents (insides) of the tag,
# not the tag itself.
# This table shows the tag name and action to take on the tag.
tag_actions = {
    'a':              'unwrap',
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


UNICODE_EM_DASH = 8212
UNICODE_ASCII_DASH = 45


def is_unicode_em_dash(s):
    if len(s.strip()) != 1:
        return False
    return ord(s.strip()) == UNICODE_EM_DASH


def convert_unicode_em_dash(s):
    if len(s.strip()) != 1:
        return s

    if is_unicode_em_dash(s):
        return chr(UNICODE_ASCII_DASH)
    else:
        return s


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

    def invalid_subname(part):
        # Not sure if this will grow, as we see more cases. This function
        # ensures we have the scaffolding to add valid parts
        valid_subname = ['text-align']
        for v in valid_subname:
            if part.strip().startswith(v):
                return not True  # Function invalid_subname returns false
        return True  # Function invalid_subname returns true

    attr_values = remove_extra_characters(attr_values)
    attr_subnames_and_values_list = []
    for part in attr_values.split(';'):
        if invalid_subname(part):
            continue
        attr_subnames_and_values_list.append(tuple(part.split(':')))
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
        if attr_name not in ['rowspan', 'colspan', 'style']:
            continue

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


def navigable_string(tag):
    if isinstance(tag, NavigableString):
        yield tag
    else:
        for child in tag.children:
            yield from navigable_string(child)


def get_number_text(text):

    text = text.strip()

    if len(text) == 1 and (text == '(' or text == ')'):
        return ''
    is_negative = True if '(' in text or ')' in text else False

    if len(text) == 1 and text == chr(UNICODE_ASCII_DASH):
        return chr(UNICODE_ASCII_DASH)

    for c in '$,% \t\n()':
        text = text.replace(c, '')
    if is_negative:
        text = '-' + text

    return text


YIELDED_STR = 0
YIELDED_NUM = 1


def strings_and_values_in_html(top_tag):
    HOW_MANY_NUMBERS_TO_CHECK_FOR_YEARS = 5
    yielded_nums = 0

    def replace_regex_whitespaces(text):
        return regex_whitespace.sub(' ', text)

    def extract_number(tag):

        nonlocal yielded_nums

        s = str(tag).strip()

        if len(s) == 1:
            s = convert_unicode_em_dash(s)

        if s == '\n':
            return

        s_num = get_number_text(s)
        if s_num == '':
            return

        if is_number(s_num):
            if len(s_num) == 1 and s_num == chr(UNICODE_ASCII_DASH):
                # print(f's_num: {s_num}')
                yielded_nums += 1
                yield (YIELDED_NUM, tag, s_num)
            elif '.' not in s_num and \
                    int(s_num) in YEARS_RANGE and \
                    yielded_nums < HOW_MANY_NUMBERS_TO_CHECK_FOR_YEARS:
                if tag.parent.string is None:
                    raise ValueError('tag.parent.string is None')
                yield (YIELDED_STR, tag, s_num)
                yield (YIELDED_NUM, tag, s_num)
                yielded_nums += 1
            else:
                # print(f's_num: {s_num}')
                yielded_nums += 1
                yield (YIELDED_NUM, tag, s_num)
        else:
            yield (YIELDED_STR, tag, replace_regex_whitespaces(s))

    for tag in navigable_string(top_tag):
        yield from extract_number(tag)


def print_navigable_string_values(html_data):
    top_tag = BeautifulSoup(html_data, 'html.parser')
    for tag in navigable_string(top_tag):
        print(f'{str(tag).strip()}', end='|')


def json_and_html_tuples(json, html):
    l1, l2 = zip(*html)
    return zip(json, l1, l2)


def update_tag_str(tag, use_str):
    # If the tag's parent only contains that one tag,
    # then the string value belonging to the tag
    # actually belongs to the parent.
    # If the tag's parent also contains a tag other than yours,
    # the the string value belonging to the tag
    # actually belongs to the tag, and not it's parent
    try:
        tag.parent.string = use_str
    except AttributeError:
        tag.string = use_str


def replace_values(json_values, html_tags_values, updated_values):
    # print_navigable_string_values(html_data)
    mappings = {}

    number_json_values = len(json_values)
    number_html_values = len(html_tags_values)
    if number_json_values != number_html_values:
        raise ValueError(f'Number of values in JSON file differs from '
                         f' number of values in HTML file '
                         f'JSON: {number_json_values} HTML: {number_html_values}\n'
                         f'json_values:\n {json_values}\n'
                         f'html_tags_values:\n{html_tags_values}')

    updated_values_count = 0
    for json_value, html_value_tag, html_value in \
          json_and_html_tuples(json_values, html_tags_values):

        print(f'(json_value, html_value): {(json_value, html_value)} ',
              f'ord: {ord(json_value[0]), ord(html_value[0])}')

        if html_value == '-':
            use_str = '999999999'
            mappings['-'] = use_str
            update_tag_str(html_value_tag, use_str)
            continue

        if html_value == json_value:
            use_str = updated_values[updated_values_count]
            mappings[html_value] = updated_values[updated_values_count]
            updated_values_count += 1
            update_tag_str(html_value_tag, use_str)
            continue

        if html_value != json_value:
            raise ValueError(f'html_value: {html_value} json_value: {json_value}\n'
                             f'Should be equal.')

    return mappings


def replace_names(names, html_tags_strings, mappings):

    number_json_names = len(names)
    number_html_names = len(html_tags_strings)
    if len(names) != len(html_tags_strings):
        raise ValueError(f'Number of names in JSON file differs from '
                         f' number of names in HTML file '
                         f'JSON: {number_json_names} HTML: {number_html_names}\n'
                         f'names:\n {names}\n'
                         f'html_tags_strings:\n{html_tags_strings}')

    for json_string, html_tag, html_string in \
          json_and_html_tuples(names, html_tags_strings):

        print(f'(json_string, html_string): {(json_string, html_string)}')

        if json_string != html_string:
            raise ValueError(
                f'Mismatched strings: ',
                f'(json_string, html_string): {(json_string, html_string)}')

        update_tag_str(html_tag, mappings[html_string])


def remove_spaces_from_strings(top_tag):

    for tag in navigable_string(top_tag):
        tag.string.replace_with(tag.string.strip())

    return top_tag


def make_html_strings_unique(html_data, names):

    append_txts = list(string.ascii_lowercase + string.ascii_uppercase)
    append_txts = list(map(lambda x: f' ({x})', append_txts))

    # Remove leading and trailing whitespaces from each
    # navigable string. The names that are input to this
    # function are from the JSON file which is created
    # by hand, and does not have any such whitespace.
    top_tag = remove_spaces_from_strings(
        BeautifulSoup(html_data, 'html.parser'))

    temp_names = names.copy()
    result = []

    while len(temp_names) > 0:
        first_name, temp_names = temp_names[0], temp_names[1:]
        if first_name in temp_names:  # name is repeated
            new_name = first_name + append_txts[0]

            found_tag = top_tag.find(text=first_name)
            if found_tag is None:
                regex_text_pattern = r'^' + re.escape(first_name)
                found_tag = top_tag.find(text=re.compile(regex_text_pattern))
                if found_tag is None:
                    raise ValueError(f'Could not find string: "{first_name}"')
            found_tag.string.replace_with(new_name)
            result.append(new_name)
            append_txts = append_txts[1:]
        else:
            result.append(first_name)

    return str(top_tag), result


# def replace_named_or_numeric(html_data):
#     html_data = html_data.encode('unicode-escape').decode()

#     result = regex_named_or_numeric.sub('', html_data)
#     return result
