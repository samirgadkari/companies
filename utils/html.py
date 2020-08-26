import re
import string
from bs4 import BeautifulSoup, NavigableString
from ml.number import is_number

regex_html_tag = re.compile(r'<[^>]+>')
regex_html_tag_or_data = re.compile(r'(<[^]]+>)|([^<]+)')
regex_tag_name = re.compile(r'<([^/ >]+?)\s[^>]*>', re.MULTILINE)
regex_tag_attrs = re.compile(r'(\w+=\"[^\"]+\"\s*)+?', re.MULTILINE)
regex_multiple_semicolons = re.compile(r'\;{2,}', re.MULTILINE)
regex_subattr_no_value = re.compile(r'\;[^\;\:]+\;', re.MULTILINE)
regex_named_or_numeric = re.compile(r'(?:\&.*?\;|\\+x..)',
                                    re.MULTILINE)

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
    for c in '$,% \t\n()':
        text = text.replace(c, '')
    return text


def replace_values(html_data, json_values, updated_str):
    top_tag = BeautifulSoup(html_data, 'html.parser')
    mappings = {}
    count = 0

    for ori_str in json_values:
        for tag in navigable_string(top_tag):
            s = str(tag)
            if s == '\n':
                continue

            s_num = get_number_text(s)

            try:
                # The comparison of the strings after stripping
                # handles the case of the original string being ' '
                # and comparing it to the '' string.
                # The float comparison is to ensure numbers like
                # '3.30' compare with '3.3'.
                # The order of comparisons is important. If the
                # original string is ' ', float(' ') will result
                # in a ValueError, which means no matching value
                # will be found. So we do the string comparison
                # before the float comparison.
                if is_number(s) and ((ori_str.strip() == s_num) or
                                     (float(ori_str) == float(s_num))):
                    # You should modify the parent of the NavigableString,
                    # not the NavigableString itself.
                    if s.strip().endswith('%'):
                        # Only 2-digit percentages are allowed,
                        # since this is what we usually see.
                        # If there are more significant digits,
                        # they will be ignored.
                        use_str = '0.' + updated_str[count][:2]
                    else:
                        use_str = updated_str[count]
                    mappings[s_num] = use_str
                    tag.parent.string = use_str
                    count += 1
                    break
            except ValueError:
                pass

    if count != len(updated_str):
        raise \
            ValueError(f'Error !! We did not process all the strings. '
                       f'count: {count}, len(updated_str): {len(updated_str)}')
    return str(top_tag), mappings


def replace_names(html_data, mappings):
    mapping_tuples = [(k, v) for k, v in mappings.items()]
    sorted_tuples = sorted(mapping_tuples, key=lambda x: len(x[0]),
                           reverse=True)

    for k, v in sorted_tuples:
        html_data = html_data.replace(k, v)

    return html_data


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
