import os

from bs4 import BeautifulSoup, NavigableString
from utils.file import get_filenames, read_file
from utils.environ import cleaned_tags_dir, tokens_file
from utils.html import get_attr_names_values
from utils.file import file_exists, remove_files, write_json_to_file
from utils.text import split_using_punctuation
from ml.tokens import remove_all_tokens_files, write_tokens_file, \
    read_tokens_file, get_tokens_filename, \
    get_token_values, flip_tokens_keys_values, is_number_token
from ml.number import Number, convert_fraction_to_whole, \
    number_to_sequence, get_number, NumberSequence


def get_sequences(filename, top_tag):
    word_num = Number.START_WORD_NUM.value
    token_seq = []
    number_dict = {}
    reverse_number_dict = {}

    def update_seq_and_number_dict(values):
        nonlocal word_num, token_seq, number_dict

        for value in values:
            # If NumberSequence, it is a number in NavigableString.
            if isinstance(value, NumberSequence):
                num_seq = value
                if num_seq in reverse_number_dict:
                    token_seq.append(reverse_number_dict[num_seq])
                else:
                    key = f'num_{word_num}'
                    number_dict[key] = num_seq
                    reverse_number_dict[num_seq] = key
                    word_num += 1
                    token_seq.append(key)
            else:
                token_seq.append(value.strip().lower())

    def recurse(tag):
        nonlocal word_num, token_seq, number_dict

        if isinstance(tag, NavigableString):
            words = []

            # We need to split the tag first, because part of the tag
            # may have $1,009 for example. If we split using punctuation,
            # we will get two words with 1 and 9 (since we're converting
            # the 009 to a number). When we put it back we will get 19.
            # Instead, we split the tag using spaces first, then check
            # if it is a number (including characters $,.()%). We extract
            # that number (excluding $,()% characters) and write
            # it to our list for further procecssing.
            for word in tag.split():
                # We want to store numbers that we find within the
                # cells of the tables with their negative sign,
                # and their % sign. We're going to output unsigned
                # integers, so we create known numbers to denote
                # - and % and start/end sequence numbers for our
                # number sequence.
                is_negative, num_str, is_percent = get_number(word)
                if num_str is not False:
                    # Many documents contain the % sign in a separate
                    # cell from the actual value. We consider the presence
                    # of the '.' in the text to denote percentage.
                    if '.' in num_str:
                        num_str = convert_fraction_to_whole(num_str)

                    # We must append the tuple here.
                    # If we extend, each value in the tuple will be
                    # separately appended and we will lose the
                    # tuple.
                    words.append(number_to_sequence(is_negative,
                                                    num_str,
                                                    is_percent))
                else:
                    for x in split_using_punctuation(word):
                        words.append(x)
            update_seq_and_number_dict(words)
        else:
            token_seq.append(tag.name.strip().lower())

            attr_names_values = []
            for name_or_value in get_attr_names_values(tag):
                for x in name_or_value.split():
                    attr_names_values.extend(split_using_punctuation(x))

            update_seq_and_number_dict(attr_names_values)
            for child in tag.children:
                recurse(child)
            token_seq.append('end_' + tag.name.strip().lower())

    def convert_dict_values(number_dict):
        result = {}
        for k, v in number_dict.items():
            result[k] = str(v)
        return result

    recurse(top_tag)

    write_json_to_file(filename + '.nums',
                       convert_dict_values(number_dict))
    return token_seq, number_dict


def find_html_table_encodings(filename, table_text, tokens):
    soup = BeautifulSoup(table_text, 'html.parser')
    file_token_seq, _ = get_sequences(filename, soup)
    tokens.update(file_token_seq)


def remove_all_number_files():
    remove_files(cleaned_tags_dir(), '**', '*.nums')


def find_all_html_table_encodings():

    remove_all_tokens_files()
    remove_all_number_files()

    # Since we're writing tokens to a file for each company,
    # and later merging these tokens, the token number
    # must always keep incrementing. This way, our dictionary with
    # (token_num: token_value) will not miss any tokens.
    current_company_dir = ''
    token_num = Number.START_WORD_NUM.value
    tokens = set()
    tokens_filename = ''
    num_dirs_to_process = 3
    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        # filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2018-01-01_2018-12-31_10-K/tables-extracted/162.table-extracted'
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
            num_dirs_to_process -= 1
            if num_dirs_to_process <= 0:
                break
        else:
            # We have to create this variable, and assign to it.
            # This way, we have access to the last filename
            # in the else clause of this for statement.
            tokens_filename = get_tokens_filename(filename,
                                                  company_dir_idx,
                                                  company_dir,
                                                  "tokens")

        find_html_table_encodings(filename, table, tokens)
        # break
    else:
        write_tokens_file(tokens, tokens_filename, token_num)

    all_tokens_filename = os.path.join(cleaned_tags_dir(), 'tokens')

    all_tokens = set()
    for filename in get_filenames(cleaned_tags_dir(), '*', 'tokens'):

        tokens = read_tokens_file(filename)
        all_tokens.update(get_token_values(tokens))

    print(f'len(all_tokens): {len(all_tokens)}')
    write_tokens_file(all_tokens, all_tokens_filename, 0)


def remove_all_encoded_files():
    remove_files(cleaned_tags_dir(), '**', '*.encoded')


def encode_html_table(filename, table_text, tokens):

    soup = BeautifulSoup(table_text, 'html.parser')
    token_seq, number_dict = get_sequences(filename, soup)

    # token_seq = clean_tokens(token_seq)

    # The encoded values are going to be all numbers.
    # To distinguish between tokens and numbers encoded using number_dict,
    # the numbers encoded with number_seq will start from the
    # maximum value of tokens + 1
    num_seq_offset = len(tokens)

    def encode(token):
        if is_number_token(token) and token in number_dict:
            return number_dict[token] + num_seq_offset
        else:
            return tokens[token]

    encoded = []
    encoded = ' '.join([encoded.extend(v) for v in
                        map(encode, token_seq)])
    with open(filename + '.encoded', 'w') as f:
        f.write(encoded)


def encode_all_html_tables():

    # Read tokens into a dictionary using value:token.
    # This allows us to write the token given each
    # value as we encode each file.
    tokens = read_tokens_file(tokens_file())
    tokens = flip_tokens_keys_values(tokens)

    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        # Ignore output files
        if filename.endswith('.encoded'):
            continue

        # Ignore files that are already processed
        if file_exists(filename + '.encoded'):
            continue

        filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2018-01-01_2018-12-31_10-K/tables-extracted/162.table-extracted'
        print(f'filename: {filename}')
        table = read_file(filename)

        encode_html_table(filename, table, tokens)
        break


if __name__ == '__main__':
    find_all_html_table_encodings()
    encode_all_html_tables()
