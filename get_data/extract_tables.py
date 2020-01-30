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
from decouple import config

HTML_FILE_SUFFIX = 'html'
TEXT_FILE_SUFFIX = 'text'

regex_contains_html = re.compile(r'<html>.*<\/html>', re.DOTALL)
regex_table = re.compile(r'<table>(.*)<\/table>', re.DOTALL)

def file_contains_html(filedata):
    if regex_contains_html.search(filedata) is not None:
        return True
    return False


def html_filename(f_name):
    return f_name + '.' + HTML_FILE_SUFFIX

def text_filename(f_name):
    return f_name + '.' + TEXT_FILE_SUFFIX

def save_file(f_name, match):

    tables = []
    for match in match.groups():
        tables.append(match)
        tables.append('\n')
    tables = ''.join(tables)

    with open(f_name, 'w') as f:
        f.write(tables)


def extract_html_tables(f_name, filedata):
    match = regex_table.match(filedata)
    save_file(html_filename(f_name), match)


# def extract_text_tables(f_name, filedata):


def extract_tables():

    filenames = glob.iglob(os.path.join(
        config('DATA_DIR'),
        '0*',
        '10-k',
        '*'))

    for f_name in filenames:
        if os.path.isfile(html_filename(f_name)) or \
           os.path.isfile(text_filename(f_name)):
           continue

        with open(f_name, 'r') as f:
            filedata = f.read()
            if file_contains_html(filedata):
                extract_html_tables(f_name, filedata)
            # else:
            #     extract_text_tables(f_name, filedata)


if __name__ == '__main__':
    extract_tables()

