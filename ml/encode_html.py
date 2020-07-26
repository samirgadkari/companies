import os

from bs4 import BeautifulSoup, NavigableString
from utils.file import get_filenames, read_file
from utils.environ import cleaned_tags_dir, tokens_file
from utils.html import get_attr_names_values, get_number
from utils.file import file_exists, remove_files, write_json_to_file
from utils.text import split_using_punctuation, remove_bad_endings, \
    filter_bad_tokens


def get_sequences(filename, top_tag):
    word_num = 0
    token_seq = []
    number_dict = {}

    def recurse(tag):
        nonlocal word_num, token_seq, number_dict

        if isinstance(tag, NavigableString):
            words = split_using_punctuation(tag)
            for word in words:
                num = get_number(word)
                if num is not False:
                    key = f'num_{word_num}'
                    number_dict[key] = num
                    word_num += 1
                    token_seq.append(key)
                else:
                    token_seq.append(word.strip().lower())
        else:
            token_seq.append(tag.name.strip().lower())
            for name_or_value in get_attr_names_values(tag):
                token_seq.append(name_or_value.strip().lower())
            for child in tag.children:
                recurse(child)
            token_seq.append('end_' + tag.name.strip().lower())

    recurse(top_tag)
    write_json_to_file(filename + '.nums', number_dict)
    return token_seq, number_dict


def find_html_table_encodings(filename, table_text, tokens):
    soup = BeautifulSoup(table_text, 'html.parser')
    file_token_seq, _ = get_sequences(filename, soup)
    tokens.update(file_token_seq)


def write_tokens_file(tokens, tokens_filename, start_token_num):
    tokens = map(remove_bad_endings, tokens)
    tokens = filter(filter_bad_tokens, tokens)
    with open(tokens_filename, 'w') as f:
        for idx, token in enumerate(tokens):
            f.write(f'{idx+start_token_num}: {token}\n')


def read_tokens_file(filename):
    tokens = {}
    with open(filename, 'r') as f:
        for line in f:
            try:
                # Don't know why this is happening, but we should
                # protect our code against it.
                if ':' not in line:
                    continue

                idx = line.index(':')
                token, value = line[:idx], line[idx+1:]
            except ValueError as e:
                print(f'line: {line}\nerror: {e}')
                raise e
            value = value.strip()
            tokens[value] = token
    return tokens


def remove_all_tokens_files():
    # You want to process all of these files at once
    # to ensure that the set of tokens takes all
    # files into consideration. This is why we
    # make sure that all token files are removed
    # before starting the process.
    print('Removing all token files ...', end=' ')
    remove_files(cleaned_tags_dir(), '**', 'tokens')


def remove_all_number_files():
    remove_files(cleaned_tags_dir(), '**', '*.nums')


def get_tokens_filename(filing_filename, company_dir_idx,
                        company_dir, tokens_filename):
    return os.path.join(filing_filename[:company_dir_idx],
                        company_dir, tokens_filename)


def find_all_html_table_encodings():

    remove_all_tokens_files()
    remove_all_number_files()

    # Since we're writing tokens to a file for each company,
    # and later merging these tokens, the token number
    # must always keep incrementing. This way, our dictionary with
    # (token_num: token_value) will not miss any tokens.
    current_company_dir = ''
    # num_dirs_to_process = 3
    token_num = 0
    tokens = set()
    tokens_filename = ''
    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        print(f'filename: {filename}')
        table = read_file(filename)

        company_dir_idx = len(cleaned_tags_dir())
        company_dir = filename[company_dir_idx+1:].split(os.sep)[0]

        if current_company_dir != company_dir:
            if len(tokens) > 0:
                write_tokens_file(tokens, tokens_filename, token_num)
                token_num += len(tokens)
                del tokens

                # print(f'num_dirs_to_process: {num_dirs_to_process}')
                # num_dirs_to_process -= 1
                # if num_dirs_to_process == 0:
                #     break

            tokens = set()
            current_company_dir = company_dir
        else:
            # We have to create this variable, and assign to it.
            # This way, we have access to the last filename
            # in the else clause of this for statement.
            tokens_filename = get_tokens_filename(filename,
                                                  company_dir_idx,
                                                  company_dir,
                                                  "tokens")

        find_html_table_encodings(filename, table, tokens)
    else:
        write_tokens_file(tokens, tokens_filename, token_num)

    all_tokens_filename = os.path.join(cleaned_tags_dir(), 'tokens')

    all_tokens = set()
    for filename in get_filenames(cleaned_tags_dir(), '*', 'tokens'):

        tokens = read_tokens_file(filename)
        all_tokens.update(tokens)

    print(f'len(tokens): {len(tokens)}')
    write_tokens_file(tokens, all_tokens_filename, 0)


def encode_html_table(filename, table_text, tokens):

    soup = BeautifulSoup(table_text, 'html.parser')
    token_seq, number_dict = get_sequences(filename, soup)

    # The encoded values are going to be all numbers.
    # To distinguish between tokens and numbers encoded using number_dict,
    # the numbers encoded with number_seq will start from the
    # maximum value of tokens + 1
    num_seq_offset = len(tokens)

    def encode(token):
        try:
            return number_dict[token] + num_seq_offset
        except KeyError:
            return tokens[token]

    encoded = ' '.join(map(encode, token_seq))
    with open(filename + '.encoded', 'w') as f:
        f.write(encoded)


def encode_all_html_tables():

    # Read tokens into a dictionary using value:token.
    # This allows us to write the token given each
    # value as we encode each file.
    tokens = read_tokens_file(tokens_file())

    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        # Ignore output files
        if '.encoded' in filename:
            continue

        # Ignore files that are already processed
        if file_exists(filename + '.encoded'):
            continue

        print(f'filename: {filename}')
        table = read_file(filename)

        encode_html_table(filename, table, tokens)


if __name__ == '__main__':
    find_all_html_table_encodings()
    encode_all_html_tables()
