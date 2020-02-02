# Extracting tables from text files is a hard task.
# There are too many patterns possible, and they
# may change any time.
# HTML tags are also used inconsistently -
# some files use <TABLE></TABLE> tags without
# any <HTML></HTML> tags in the file.
# Also, even when they use table tags, the table
# inside is in plain text - there are no <TR>, <TD>.
#
# Maybe it just makes sense to use NLP to extract
# tables from all types of files (HTML and text).

import re
import os
import glob
import html
from decouple import config

TABLES_EXTRACTED_FILE_SUFFIX = 'tables_extracted'

regex_table = re.compile(r'<TABLE.*?>(.*?)<\/TABLE>',
                         flags=re.DOTALL | \
                                re.IGNORECASE)

num_files_extracted = 0
num_files_extraction_error = 0

def tables_extracted_filename(f_name):
    return f_name + '.' + TABLES_EXTRACTED_FILE_SUFFIX

def save_file(f_name, matches):

    matches = ['<TABLE>' + match + '</TABLE>\n\n\n'
               for match in matches]
    tables = ''.join(matches)
    with open(f_name, 'w') as f:
        f.write(tables)


def extract_tables(f_name, filedata):
    global num_files_extracted
    global num_files_extraction_error

    matches = regex_table.findall(filedata)
    if len(matches) == 0:
        num_files_extraction_error += 1
        print('{:30s}: {:5d} {}'.format('num_files_extraction_error',
                                        num_files_extraction_error,
                                        f_name))
    else:
        save_file(tables_extracted_filename(f_name), matches)
        num_files_extracted += 1
        print('{:30s}: {:5d}'.format('num_files_extracted',
                                     num_files_extracted))


def extract_tables_from_files():

    filenames = glob.iglob(os.path.join(
                           config('DATA_DIR'),
                           '0*',
                           '10-k',
                           '*'))

    # import pdb; pdb.set_trace()

    filenames = [fn for fn in filenames if 'tables_extracted' not in fn]
    # count = 0
    for f_name in filenames:
        # count += 1
        # if count > 2:
        #     return
        if os.path.isfile(tables_extracted_filename(f_name)):
           continue

        with open(f_name, 'r') as f:
            filedata = html.unescape(f.read())
            with open('temp.extracted', 'w') as f:
                f.write(filedata)

            extract_tables(f_name, filedata)

if __name__ == '__main__':
    extract_tables_from_files()

