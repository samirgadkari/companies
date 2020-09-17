import os
from utils.file import remove_files, read_file, get_filenames
from utils.environ import cleaned_tags_dir, generated_data_dir, tokens_file
from ml.tokens import write_tokens_file, remove_all_tokens_files, \
    get_tokens_filename, read_tokens_file, get_token_values, \
    flip_tokens_keys_values
from ml.number import Number
from ml.encode_html import find_html_table_encodings, \
    encode_html_table
from ml.encode_json import find_json_encodings, encode_json
from ml.validation_test_split import matching_filenames, FILETYPE_TRAINING, \
    FILETYPE_VALIDATION, FILETYPE_TESTING


def remove_all_number_files():
    remove_files(cleaned_tags_dir(), '**', '*.nums')


def all_encodings(filenames, base_dirname, tokens_path):

    # Since we're writing tokens to a file for each company,
    # and later merging these tokens, the token number
    # must always keep incrementing. This way, our dictionary with
    # (token_num: token_value) will not miss any tokens.
    current_company_dir = ''
    token_num = Number.START_WORD_NUM.value
    tokens = set()
    tokens_filename = ''
    # num_dirs_to_process = 3
    for filename in filenames:
        # filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2018-01-01_2018-12-31_10-K/tables-extracted/162.table-extracted'
        print(f'filename: {filename}')
        text = read_file(filename)

        company_dir_idx = len(base_dirname)
        if base_dirname == generated_data_dir():
            company_dir = ''
        else:
            company_dir = filename[company_dir_idx+1:].split(os.sep)[0]

        if current_company_dir != company_dir:
            if len(tokens) > 0:
                write_tokens_file(tokens, tokens_filename, token_num)
                token_num += len(tokens)
                del tokens

            tokens = set()
            current_company_dir = company_dir
            # num_dirs_to_process -= 1
            # if num_dirs_to_process <= 0:
            #     break
        else:
            # We have to create this variable, and assign to it.
            # This way, we have access to the last filename
            # in the else clause of this for statement.
            tokens_filename = get_tokens_filename(filename,
                                                  company_dir_idx,
                                                  company_dir,
                                                  "tokens")

        if filename.endswith('unescaped') or filename.endswith('html') \
           or filename.endswith('table-extracted'):
            find_html_table_encodings(filename, text, tokens)
        elif filename.endswith('json'):
            find_json_encodings(filename, text, tokens)
    else:
        write_tokens_file(tokens, tokens_filename, token_num)

    all_tokens_filename = os.path.join(base_dirname, 'tokens')

    all_tokens = set()
    for filename in get_filenames(tokens_path):

        tokens, _ = read_tokens_file(filename)
        all_tokens.update(get_token_values(tokens))

    print(f'len(all_tokens): {len(all_tokens)}')

    # We need to give the offset as the last value in this function call.
    # This allows us to interpret the value of 1 as the start of a
    # number sequence, and not confuse it with an entry in the tokens
    # file that has key = 1.
    write_tokens_file(all_tokens, all_tokens_filename,
                      Number.START_WORD_NUM.value)


def find_all_encodings(file_type, paths, saved_filenames_path, tokens_path):
    filenames = matching_filenames(saved_filenames_path,
                                   paths,
                                   file_type)
    print('Starting all encodings')
    base_dirname = os.sep.join(saved_filenames_path.split(os.sep)[:-1])
    all_encodings(filenames, base_dirname, tokens_path)


def find_training_encodings():
    paths = [os.path.join(generated_data_dir(), '*.unescaped'),
             os.path.join(generated_data_dir(), '*.expected_json')]
    saved_filenames_path = os.path.join(generated_data_dir(),
                                        'training_filenames')
    tokens_path = os.path.join(generated_data_dir(), 'tokens')
    find_all_encodings(FILETYPE_TRAINING, paths, saved_filenames_path,
                       tokens_path)


def find_validation_encodings():
    paths = [os.path.join(cleaned_tags_dir(),
                          '*', '10-k', '*', '*', '*.unescaped')]
    saved_filenames_path = os.path.join(cleaned_tags_dir(),
                                        'validation_test_split')
    remove_all_tokens_files()
    remove_all_number_files()

    tokens_path = os.path.join(cleaned_tags_dir(), '*', 'tokens')
    find_all_encodings(FILETYPE_VALIDATION, paths, saved_filenames_path,
                       tokens_path)


def find_test_encodings():
    paths = [os.path.join(cleaned_tags_dir(),
                          '*', '10-k', '*', '*', '*.unescaped')]
    saved_filenames_path = os.path.join(cleaned_tags_dir(),
                                        'validation_test_split')
    remove_all_tokens_files()
    remove_all_number_files()

    tokens_path = os.path.join(cleaned_tags_dir(), '*', 'tokens')
    find_all_encodings(FILETYPE_TESTING, paths, saved_filenames_path,
                       tokens_path)


def remove_all_encoded_files(paths):
    remove_files(*paths)


def encode_all_html_tables(file_type, paths,
                           saved_filenames_path, tokens_path):

    # Read tokens into a dictionary using value:token.
    # This allows us to write the token given each
    # value as we encode each file.
    tokens, encoded_num_start_value_shift = read_tokens_file(tokens_path)
    tokens = flip_tokens_keys_values(tokens)

    # num_dirs_to_process = 3
    # current_company_dir = ''

    filenames = matching_filenames(saved_filenames_path,
                                   paths,
                                   file_type)
    for filename in filenames:

        # company_dir_idx = len(cleaned_tags_dir())
        # company_dir = filename[company_dir_idx+1:].split(os.sep)[0]

        # if current_company_dir != company_dir:
        #     current_company_dir = company_dir
        #     num_dirs_to_process -= 1
        #     if num_dirs_to_process <= 0:
        #         break

        # filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2018-01-01_2018-12-31_10-K/tables-extracted/162.table-extracted'
        print(f'filename: {filename}')
        file_data = read_file(filename)

        if filename.endswith('json'):
            encode_json(filename, file_data, tokens,
                        encoded_num_start_value_shift)
        else:
            encode_html_table(filename, file_data, tokens,
                              encoded_num_start_value_shift)


def encode_training_files():
    paths = [os.path.join(generated_data_dir(), '*.unescaped'),
             os.path.join(generated_data_dir(), '*.expected_json')]
    saved_filenames_path = os.path.join(generated_data_dir(),
                                        'training_filenames')
    tokens_path = os.path.join(generated_data_dir(), 'tokens')
    encode_all_html_tables(FILETYPE_TRAINING, paths,
                           saved_filenames_path, tokens_path)


def encode_validation_files():
    paths = [os.path.join(cleaned_tags_dir(),
                          '*', '10-k', '*', '*', '*.unescaped')]
    saved_filenames_path = os.path.join(cleaned_tags_dir(),
                                        'validation_test_split')
    tokens_path = os.path.join(cleaned_tags_dir(), '*', 'tokens')
    encode_all_html_tables(FILETYPE_VALIDATION, paths,
                           saved_filenames_path, tokens_path)


def encode_test_files():
    paths = [os.path.join(cleaned_tags_dir(),
                          '*', '10-k', '*', '*', '*.unescaped')]
    saved_filenames_path = os.path.join(cleaned_tags_dir(),
                                        'validation_test_split')
    tokens_path = os.path.join(cleaned_tags_dir(), '*', 'tokens')
    encode_all_html_tables(FILETYPE_TESTING, paths,
                           saved_filenames_path, tokens_path)


if __name__ == '__main__':
    find_all_encodings(FILETYPE_TRAINING)
    # encode()
