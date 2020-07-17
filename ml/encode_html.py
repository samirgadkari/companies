import os
from bs4 import BeautifulSoup
from utils.file import (get_filenames, read_file, write_file,
                        ensure_dir_exists)
from utils.environ import cleaned_tags_dir, encoded_tables_dir
from utils.html import get_attr_names_values, find_numbers


def update_tag_names(tag, tag_names):

    for tag in tag.descendants:
        tag_names.add(tag.name)
    return tag_names


def update_tag_attrs_names_values(tag, tag_attr_names, tag_attr_values):

    for tag in tag.descendants:
        for name, value in get_attr_names_values(tag):

            tag_attr_names.update(name)
            if isinstance(value, list):
                subnames, subvalues = zip(*value)
                tag_attr_names.update(subnames)
                tag_attr_values.update(subvalues)
            else:
                print(f'values: {value}')
                print(f'type(values): {type(value)}')
                tag_attr_values.update(value)


def convert_numbers(tag, tag_text_numbers):

    text = ' '.join(tag.stripped_strings)
    tag_text_numbers.update(find_numbers(text))


def find_html_table_encodings(table_text, tag_names,
                              tag_attr_names, tag_attr_values,
                              tag_text_numbers):

    soup = BeautifulSoup(table_text, 'html.parser')
    update_tag_names(soup, tag_names)
    update_tag_attrs_names_values(soup, tag_attr_names, tag_attr_values)
    convert_numbers(soup, tag_text_numbers)


def find_all_html_table_encodings():
    tag_names = set()
    tag_attr_names = set()
    tag_attr_values = set()
    tag_text_numbers = set()
    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        print(f'filename: {filename}')
        table = read_file(filename)

        find_html_table_encodings(table, tag_names,
                                  tag_attr_names,
                                  tag_attr_values,
                                  tag_text_numbers)
        break

    num_tag_names, num_tag_attr_names, num_tag_attr_values, \
        num_tag_text_numbers = map(len, [tag_names, tag_attr_names,
                                         tag_attr_values, tag_text_numbers])
    print(f'#names: {num_tag_names}\n'
          '#attrs: {num_tag_attr_names}\n'
          '#values: {num_tag_attr_values}\n'
          '#numbers: {num_tag_text_numbers}\n')
    combined_set = set().update(tag_names) \
                        .update(tag_attr_names) \
                        .update(tag_attr_values) \
                        .update(tag_text_numbers)
    print(f'total_unique_values: {len(combined_set)}')

    # Encode tag names starting at 100000
    # Encode attr names starting at 200000
    # Encode attr values starting at 300000
    # All numbers will be encoded starting at 400000.
    # Since neural networks require 32-bit values,
    # we can accomodate 4 Billion - 400000 values and use
    # a single scalar value per word/number.


def encode_all_html_tables():

    return

    tag_names = set()
    tag_attr_names = set()
    tag_attr_values = set()
    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        print(f'filename: {filename}')
        table = read_file(filename)

        encode_html_table(table, tag_names, tag_attr_names, tag_attr_values)

        filename_suffix = filename[len(cleaned_tags_dir()):]
        out_filename = encoded_tables_dir() + filename_suffix
        out_dirname_parts = out_filename.split(os.sep)[:-1]
        ensure_dir_exists(os.path.join(os.sep, *out_dirname_parts))

        write_file(out_filename, str(table_tag))


if __name__ == '__main__':
    find_all_html_table_encodings()
    encode_all_html_tables()
