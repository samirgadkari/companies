import os
import html
from utils.file import read_file, write_file, get_filenames
from utils.environ import html_samples_dir


def unescape_all_tables(search_path):
    for filename in get_filenames(search_path):
        print(f'Un-escaping file: {filename}')
        parts = filename.split('.')
        out_filename = '.'.join(parts[:-1]) + '.unescaped'
        converted = html.unescape(read_file(filename))
        write_file(out_filename, converted)
