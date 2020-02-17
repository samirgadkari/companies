import re
import os
import sys
import glob
import html
from utils.html_utils import replace_html_tags
from decouple import config

TABLES_EXTRACTED_DIR_SUFFIX = 'tables-extracted'
TABLES_EXTRACTED_FILE_SUFFIX = 'table-extracted'

TEXT_FILE_TYPE = 0
HTML_FILE_TYPE = 1

# Get everything except the table tags since this is for text.
regex_table_for_text = re.compile(r'(<TABLE.*?>.*?<\/TABLE>)',
                                  flags=re.DOTALL | \
                                  re.IGNORECASE)

# Get everything including the table tags since this is html.
regex_table_for_html = re.compile(r'(<TABLE.*?>.*?<\/TABLE>)',
                                  flags=re.DOTALL | \
                                  re.IGNORECASE)

regex_xbrl_file = re.compile(r'<XBRL>',
                             flags=re.DOTALL | \
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
    upper_case_body_tags = [s in filedata for s in ['<BODY', '/BODY']]
    lower_case_body_tags = [s in filedata for s in ['<body', '/body']]
    return upper_case_body_tags or lower_case_body_tags


# This seems to not work, probably because the current
# HTML spec is different. Online validators report
# errors in the older HTML text.
#
# from bs4 import BeautifulSoup
# def extract_html_tables(filedata):
#     soup = BeautifulSoup(filedata, 'html.parser')
#     return soup.find_all('table', recursive=False)


def save_files(dir_name, file_type, matches):
    print(f'file_type: {file_type}')
    for id, match in enumerate(matches, start=-1):

        if id == -1:  # Ignore the first match (which is the full match)
            continue

        if file_type == TEXT_FILE_TYPE:
            match = replace_html_tags(match)
        f_name = extracted_tables_filename(dir_name, id)
        write_extracted_table_file(f_name, match)


def save_tables(matches, f_name, file_type):
    if len(matches) == 0:
        return False
    else:
        save_files(tables_extracted_dirname(f_name), file_type, matches)
        return True


def extract_tables():
    global num_files_extracted
    global num_files_extraction_error

    filenames = list(glob.iglob(os.path.join(
                                    config('DATA_DIR'),
                                    '0*',
                                    '10-k',
                                    '*')))

    xbrl_files = 0
    files_read = 0
    num_files = len(filenames)
    for f_name in filenames:
        print(f'Processing file: {f_name}')
        with open(f_name, 'r') as f:
            filedata = html.unescape(f.read())

        files_read += 1
        if is_xbrl_file(filedata):
            print('  xbrl file')
            xbrl_files += 1  # ignore XBRL files for now
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

