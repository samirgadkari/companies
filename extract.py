import os
import re
import glob
import html
from bs4 import BeautifulSoup
from utils.environ import data_dir
from utils.file import get_filenames

TABLES_EXTRACTED_DIR_SUFFIX = 'tables-extracted'
TABLES_EXTRACTED_FILE_SUFFIX = 'table-extracted'

TEXT_FILE_TYPE = 0
HTML_FILE_TYPE = 1
MIN_TABLE_SIZE = 10240  # 10KB


# Get everything including the table tags.
regex_table_for_text = re.compile(r'(<TABLE.*?>.*?<\/TABLE>)',
                                  flags=re.DOTALL |
                                  re.IGNORECASE)

# Get everything including the table tags.
regex_table_for_html = re.compile(r'(<TABLE.*?>.*?<\/TABLE>)',
                                  flags=re.DOTALL | re.IGNORECASE)

regex_xbrl_file = re.compile(r'<XBRL>',
                             flags=re.DOTALL | re.IGNORECASE)

regex_balance_sheet = \
    re.compile(r'Consolidated Balance Sheets?',
               re.MULTILINE)
table_balance_sheet_name = 'Consolidated Balance Sheet'


def get_data(filedata, search_regex, table_name, search_tag):
    def num_contained_tags(tag, contained_tag_name):
        return len(tag.find_all(contained_tag_name))

    def contains_single_tag(containing_tag, contained_tag_name):
        while containing_tag is not None:

            # If the tag name we're looking for is inside
            # the tag we're looking for,
            # return the tag.
            print(f'containing_tag.name: {containing_tag.name}, '
                  f'search_tag: {search_tag}')
            if containing_tag.name == search_tag:
                return containing_tag

            num_tags = num_contained_tags(
                containing_tag, contained_tag_name)

            print(f'tag.name: {contained_tag_name}, num_tags: {num_tags}')
            if num_tags > 1:
                break
            elif num_tags == 1:
                return containing_tag

            containing_tag = containing_tag.parent

        return None

    soup = BeautifulSoup(filedata, 'html.parser')

    text_tags = soup.find_all(string=search_regex)
    print(f'len(text_tags): {len(text_tags)}')

    good_tags = []
    i = 0
    for text_tag in text_tags:
        python_string_text_tag = text_tag.encode('utf-8').decode('utf-8')
        # print(f'{python_string_text_tag}')
        if (python_string_text_tag != table_name) and \
           (python_string_text_tag != table_name + 's'):
            # print(f'{python_string_text_tag} !='
            #       f'table_name (including plural name)')
            continue

        print(f'i: {i}')
        i += 1
        good_tag = contains_single_tag(text_tag.parent, search_tag)
        if good_tag is not None:
            good_tags.append(good_tag)

    return good_tags


def extract_single_table(filename):
    with open(filename, 'r') as f:
        filedata = html.unescape(f.read())

    tags = get_data(filedata, regex_balance_sheet,
                   table_balance_sheet_name, 'table')
    if tags is not None:
        tag_num = 0
        for tag in tags:
            # print(tag.prettify())
            print(f'Extracted table for filename: {filename}')
            with open(filename + '_' + str(tag_num) + '.html', 'w') as f:
                f.write(tag.prettify())
                tag_num += 1
    else:
        print(f'Could not extract single table for filename: {filename}')


def extract_all_tables():
    i = 0
    search_path = os.path.join(data_dir(), '00*', '10-k', '*')
    print(f'search_path: {search_path}')
    for filename in glob.iglob(search_path):
        if i > 20:
            break
        print(f'Extracting[{i}]: {filename}')
        extract_single_table(filename)
        i += 1


if __name__ == '__main__':
    extract_all_tables()
