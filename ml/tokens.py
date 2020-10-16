import os
import re
import string
import numpy as np
from ml.clean_tables import tag_actions
from utils.environ import cleaned_tags_dir, generated_data_dir
from utils.file import remove_files, get_json_from_file, \
    write_json_to_file


class Tokens():

    def __init__(self):
        self.all_chars = self.set_of_all_chars_in_data()

        self.regex_number_token = re.compile(r'^num\_\d+$')
        self.MIN_DATA_SIZE = 5
        self.MAX_DATA_SIZE = 20

        self.NUM_TOKENS = 1000

        self.tokens_fn = os.path.join(generated_data_dir(), 'tokens')
        if os.path.exists(self.tokens_fn):
            self.tokens = get_json_from_file(self.tokens_fn)
        else:
            self.tokens = self.create_tokens()


    def set_of_all_chars_in_data(self):

        all_chars = list(string.ascii_lowercase)
        all_chars.extend(string.ascii_uppercase)
        all_chars.extend(string.digits)
        # all_chars.extend(' ' * 5)

        # We convert it to a set first to ensure that there are no
        # duplicate characters
        all_chars = list(set(all_chars))
        return all_chars


    def special_tokens(self):
        return ['-']


    def html_structure_tokens(self):
        html_tokens = list(filter(lambda x: x is not None, tag_actions.keys()))
        html_end_tokens = ['end_' + x for x in html_tokens]
        html_tokens.extend(html_end_tokens)
        return html_tokens


    def json_structure_tokens(self):
        json_tokens = list('\{\}\[\]\:\"\,')
        json_tokens.extend(['name', 'values', 'header', 'table_data'])
        return json_tokens


    def create_tokens(self):

        lengths = np.random.randint(self.MIN_DATA_SIZE,
                                    self.MAX_DATA_SIZE + 1,
                                    self.NUM_TOKENS)

        all_tokens = ['<sos>', '<pad>', '<eos>']
        all_tokens.extend(self.special_tokens())
        all_tokens.extend(self.html_structure_tokens())
        all_tokens.extend(self.json_structure_tokens())

        all_tokens.extend([''.join(np.random.choice(self.all_chars, length))
                           for length in lengths])

        all_tokens = [x.strip() for x in all_tokens]
        write_json_to_file(self.tokens_fn, all_tokens)

        return all_tokens





# TODO: These are left-over from earlier implementations.
# Make sure to remove all the code that uses them
# as well as these functions (from here to end of the file).

def clean_tokens(tokens):
    return \
        list(filter(lambda token:
                    False if token.startswith('num_') else True,
                    tokens))


def write_tokens_file(tokens, tokens_filename, start_token_num):
    # This function is called when we're finding all tokens.
    # At this time, all 'nums_*' tokens are saved to the
    # table's individual file. We should not use 'nums_*' from
    # the global tokens file, so we remove them.
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

    # Start value of an encoded number can equal a token value.
    # Calculate the shift to be the maximum token value + 1
    # if len(tokens) > 0:
    #     token_keys_as_integers = map(int, tokens.keys())
    #     encoded_num_start_value_shift = max(token_keys_as_integers) + 1
    #     return tokens, encoded_num_start_value_shift
    # else:
    #     return tokens, None
    return tokens


def get_token_values(tokens):
    return set([value for value in tokens.values()])


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


def flip_tokens_keys_values(tokens):
    return {v: k for k, v in tokens.items()}


# def compare_tokens(t1, t2):
#     if not isinstance(t1, np.ndarray) or \
#        not isinstance(t2, np.ndarray):
#         raise ValueError('Pass in numpy arrays for speedy comparison.')
#     num_diff = np.abs(len(t1) - len(t2))
#     check_len = min(len(t1), len(t2))
#     num_diff += np.sum(t1[:check_len] != t2[:check_len])
#     return num_diff
