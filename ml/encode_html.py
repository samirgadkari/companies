import os

from bs4 import BeautifulSoup, NavigableString
from utils.file import (get_filenames, read_file, write_file,
                        ensure_dir_exists)
from utils.environ import cleaned_tags_dir, encoded_tables_dir
from utils.html import get_attr_names_values, get_number
from utils.file import write_json_to_file


def get_token_sequence(filename, top_tag):
    word_num = 0
    token_seq = []
    number_seq = []

    def recurse(tag):
        nonlocal word_num

        if isinstance(tag, NavigableString):
            words = str(tag).split()
            for word in words:
                num = get_number(word)
                if num is not False:
                    key = f'num_{word_num}'
                    number_seq.append((key, num))
                    word_num += 1
                    token_seq.append(key)
                else:
                    token_seq.append(word)
        else:
            token_seq.append(tag.name)
            for name_or_value in get_attr_names_values(tag):
                token_seq.append(name_or_value)
            for child in tag.children:
                recurse(child)
            token_seq.append('end_' + tag.name)

    recurse(top_tag)
    write_json_to_file(filename + '.nums', number_seq)
    return token_seq


def find_html_table_encodings(filename, table_text, token_seq, tokens):
    soup = BeautifulSoup(table_text, 'html.parser')
    seq = get_token_sequence(filename, soup)
    token_seq.extend(seq)
    tokens.update(seq)


def find_all_html_table_encodings():
    token_seq = []
    tokens = set()
    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2012-01-01_2012-12-31_10-K/tables-extracted/100.table-extracted'
        print(f'filename: {filename}')
        table = read_file(filename)

        find_html_table_encodings(filename, table, token_seq, tokens)
        break

    print(f'token_seq: {token_seq}')
    print(f'len(token_seq): {len(token_seq)}')
    print(f'tokens: {tokens}')
    print(f'len(tokens): {len(tokens)}')

    tokens_filename = os.path.join(cleaned_tags_dir(),
                                   'tokens')
    with open(tokens_filename, 'w') as f:
        for idx, token in enumerate(tokens):
            f.write(f'{idx}: {token}\n')


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
