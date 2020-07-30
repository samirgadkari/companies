import os
import re
from utils.environ import cleaned_tags_dir
from utils.file import remove_files

regex_number_token = re.compile(r'^num\_\d+$')


def clean_tokens(tokens):
    return \
        list(filter(lambda token:
                    False if token.startswith('num_') else True,
                    tokens))


def write_tokens_file(tokens, tokens_filename, start_token_num):
    tokens = clean_tokens(tokens)
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
                key, value = line[:idx], line[idx+1:]
            except ValueError as e:
                print(f'line: {line}\nerror: {e}')
                raise e
            value = value.strip()
            tokens[key] = value
    return tokens


def get_token_values(tokens):
    return set([value for value in tokens.values()])


def flip_tokens_keys_values(tokens):
    return {v: k for k, v in tokens.items()}


def remove_all_tokens_files():
    # You want to process all of these files at once
    # to ensure that the set of tokens takes all
    # files into consideration. This is why we
    # make sure that all token files are removed
    # before starting the process.
    print('Removing all token files ...', end=' ')
    remove_files(cleaned_tags_dir(), '**', 'tokens')


def get_tokens_filename(filing_filename, company_dir_idx,
                        company_dir, tokens_filename):
    return os.path.join(filing_filename[:company_dir_idx],
                        company_dir, tokens_filename)


def is_number_token(token):
    return False if regex_number_token.match(token) is None else True