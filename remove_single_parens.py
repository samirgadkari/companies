import os
import re
import html
from utils.environ import generated_html_json_dir
from utils.html import is_number, navigable_string, handle_single_parens
from bs4 import BeautifulSoup
from utils.file import read_file, write_file, get_filenames
from utils.environ import html_samples_dir

def remove_single_parens(search_path):

    for filename in get_filenames(search_path):
        # filename = '/Volumes/datadrive/generated-html-json/0001035713_providian_financial_corp__10-k__2004-01-01_2004-12-31_10-k__tables-extracted_split-tables__24.table-extracted'

        print(f'Removing single parens from file: {filename}')
        parts = filename.split('.')
        out_filename = '.'.join(parts[:-1]) + '.remove-single-parens'

        top_tag = handle_single_parens(read_file(filename))
        write_file(out_filename, str(top_tag))


if __name__ == '__main__':
    remove_single_parens(os.path.join(generated_html_json_dir(),
                                      '*.table-extracted'))
