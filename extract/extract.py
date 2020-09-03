'''
Extract tables from HTML/XBRL files in an input directory,
and put the resulting files in an output directory -
one table per file.
'''
import os
import re
import glob
import html
from bs4 import BeautifulSoup
from utils.environ import data_dir, extracted_tables_dir
from utils.html import replace_html_tags

TABLES_EXTRACTED_DIR_SUFFIX = os.path.split(extracted_tables_dir())[1]
TABLES_EXTRACTED_FILE_SUFFIX = 'table-extracted'

HTML_FILE_TYPE = 0
TEXT_FILE_TYPE = 1
XBRL_FILE_TYPE = 2
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


def tables_extracted_dirname(f_name):

    prefix, date_range = os.path.split(f_name)
    prefix, filing_type = os.path.split(prefix)
    _, company_name = os.path.split(prefix)

    dir_name = os.path.join(os.path.split(data_dir())[0],
                            TABLES_EXTRACTED_DIR_SUFFIX,
                            company_name,
                            filing_type,
                            date_range)
    return dir_name


def extracted_tables_filename(dir_name, id):
    return os.path.join(dir_name,
                        TABLES_EXTRACTED_DIR_SUFFIX,
                        f'{id}.{TABLES_EXTRACTED_FILE_SUFFIX}')


def write_extracted_table_file(filename, filedata):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(filedata)


def save_files(dir_name, file_type, matches):
    id = 0
    # Ignore the first match, since it is the full match
    for match in matches[1:]:

        # Ignore small tables - many times they're just formatting.
        if len(match) < MIN_TABLE_SIZE:
            continue

        if file_type == TEXT_FILE_TYPE:
            match = replace_html_tags(match)
        if file_type == HTML_FILE_TYPE:
            match = prettify_html(match)

        filename = extracted_tables_filename(dir_name, id)
        write_extracted_table_file(filename, match)
        id += 1


def save_tables(matches, filename, file_type):
    if len(matches) == 0:
        return False
    else:
        save_files(tables_extracted_dirname(filename), file_type, matches)
        return True


def is_xbrl_file(filedata):
    upper_case_xbrl_tags = \
        all([s in filedata for s in ['<XBRL', '</XBRL']])
    lower_case_xbrl_tags = \
        all([s in filedata for s in ['<xbrl', '</xbrl']])
    return upper_case_xbrl_tags or lower_case_xbrl_tags


def is_html_file(filedata):
    upper_case_body_tags = \
        all([s in filedata for s in ['<BODY', '/BODY']])
    lower_case_body_tags = \
        all([s in filedata for s in ['<body', '/body']])
    return upper_case_body_tags or lower_case_body_tags


def prettify_html(data):
    result = data
    try:
        soup = BeautifulSoup(data, 'html.parser')
        result = soup.prettify()
    except RecursionError as e:
        print('Recursion Error occurred - dont prettify HTML')
    return result


def get_tables_from_single_file(top_input_dirname,
                                filename, top_output_dirname,
                                num_files_of_type):
    with open(filename, 'r') as f:
        filedata = html.unescape(f.read())

    if is_xbrl_file(filedata):
        # Although it says XBRL, it can be processed as HTML
        print('  xbrl file')
        matches = regex_table_for_html.findall(filedata)
        tables_saved = save_tables(matches, filename, HTML_FILE_TYPE)
        num_files_of_type[XBRL_FILE_TYPE] += 1
    else:
        if is_html_file(filedata):
            print('  html file')
            matches = regex_table_for_html.findall(filedata)
            tables_saved = save_tables(matches, filename, HTML_FILE_TYPE)
            num_files_of_type[HTML_FILE_TYPE] += 1
        else:
            num_files_of_type[TEXT_FILE_TYPE] += 1
            # We don't have the code to deal with text files yet.
            return
            # print('  text file')
            # matches = regex_table_for_text.findall(filedata)
            # tables_saved = save_tables(matches, filename, TEXT_FILE_TYPE)

    if tables_saved is False:
        print(f' >>> Error extracting file: {filename}')


def extract_all_tables():
    top_input_dirname = data_dir()
    search_path = os.path.join(data_dir(), '00*', '10-k', '*')
    output_dirname = extracted_tables_dir()

    i = 0
    num_files_of_type = [0, 0, 0]
    print(f'search_path: {search_path}')
    for filename in glob.iglob(search_path):
        # if i > 20:
        #     break
        print(f'Extracting[{i}]: {filename}', end='')
        get_tables_from_single_file(top_input_dirname, filename,
                                    output_dirname, num_files_of_type)
        print(f'num_files_of_type: {num_files_of_type}')
        i += 1


if __name__ == '__main__':
    extract_all_tables()
