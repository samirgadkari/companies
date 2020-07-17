import re
import os
import sys
import glob
import html
from decouple import config
from bs4 import BeautifulSoup
from utils.html import replace_html_tags

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
                                  flags=re.DOTALL |
                                  re.IGNORECASE)

regex_xbrl_file = re.compile(r'<XBRL>',
                             flags=re.DOTALL |
                             re.IGNORECASE)

num_files_extracted = 0
num_files_extraction_error = 0


def tables_extracted_dirname(f_name):
    prefix, date_range = os.path.split(f_name)
    prefix, filing_type = os.path.split(prefix)
    _, company_name = os.path.split(prefix)

    dir_name = os.path.join(os.path.split(config('DATA_DIR'))[0],
                            TABLES_EXTRACTED_DIR_SUFFIX,
                            company_name,
                            filing_type,
                            date_range)
    return dir_name


def extracted_files_exists_for(f_name):
    extracted_dirname = os.path.join(config('EXTRACTED_TABLES_DIR'),
                                     os.path.split(f_name)[-1])
    return os.path.exists(extracted_dirname)


def unprocessed_files(fns):
    last_file_first = fns[::-1]
    for id, fn in enumerate(last_file_first):
        if extracted_files_exists_for(fn):
            files_to_process = last_file_first[:id][::-1]
            return len(files_to_process), files_to_process
    print('All files already processed !!')
    return 0, []

def extracted_tables_filename(dir_name, id):
    return os.path.join(dir_name,
                        TABLES_EXTRACTED_DIR_SUFFIX,
                        f'{id}.{TABLES_EXTRACTED_FILE_SUFFIX}')


def write_extracted_table_file(f_name, filedata):
    os.makedirs(os.path.dirname(f_name), exist_ok=True)
    with open(f_name, 'w') as f:
        f.write(filedata)


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

def save_files(dir_name, file_type, matches):
    print(f'file_type: {file_type}')

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

        f_name = extracted_tables_filename(dir_name, id)
        write_extracted_table_file(f_name, match)
        id += 1


def save_tables(matches, f_name, file_type):
    if len(matches) == 0:
        return False
    else:
        save_files(tables_extracted_dirname(f_name), file_type, matches)
        return True


def extract_tables():
    global num_files_extracted
    global num_files_extraction_error

    filename = os.path.join(config('DATA_DIR'), 'filtered_filenames')
    with open(filename, 'r') as f:
        fns = f.read().split('\n')

    fns_len, fns = unprocessed_files(fns)
    if fns_len == 0:
        return

    filenames = []
    for fn in fns:
        filenames.extend(list(glob.iglob(os.path.join(fn, '10-k', '*'))))

    xbrl_files = 0
    files_read = 0
    num_files = len(filenames)
    for f_name in filenames:
        print(f'Processing file: {f_name}')
        if extracted_files_exists_for(f_name):
            print(f'File exists: {f_name}')
            continue

        with open(f_name, 'r') as f:
            filedata = html.unescape(f.read())

        files_read += 1
        if is_xbrl_file(filedata):
            print('  xbrl file')
            xbrl_files += 1  # Treat XBRL files as HTML files.
                             # Here we're finding out their percentage
                             # in our dataset.
                             # Find out how to process them
                             # as XBRL later.
            matches = regex_table_for_html.findall(filedata)
            tables_saved = save_tables(matches, f_name, HTML_FILE_TYPE)
        else:
            if is_html_file(filedata):
                print('  html file')
                matches = regex_table_for_html.findall(filedata)
                tables_saved = save_tables(matches, f_name, HTML_FILE_TYPE)
            else:
                print('  text file')
                matches = regex_table_for_text.findall(filedata)
                tables_saved = save_tables(matches, f_name, TEXT_FILE_TYPE)

            if tables_saved == False:
                num_files_extraction_error += 1
                print('{:30s}: {:5d} {}'.format('num_files_extraction_error',
                                                num_files_extraction_error,
                                                f_name))
            else:
                num_files_extracted += 1
                print('{:30s}: {:5d}'.format('num_files_extracted',
                                                 num_files_extracted))
        print(f'num_files: {num_files}, xbrl_files: {xbrl_files}, '
              f'files_read: {files_read}, '
              f'percent_xbrl_files: {xbrl_files/files_read}')


if __name__ == '__main__':
    extract_tables()

