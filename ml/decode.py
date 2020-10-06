import os
import sys
from utils.environ import tokens_file, cleaned_tags_dir, \
    generated_data_dir
from ml.tokens import read_tokens_file
from ml.number import Number, convert_whole_to_fraction
from utils.file import write_file, remove_files, \
    get_filenames, create_dirs


def decode_file(filename, tokens):

    with open(filename, 'r') as f:
        numbers = list(map(int, f.read().split()))

        result = []
        idx = 0
        while(idx < len(numbers)):

            num = numbers[idx]
            if num == Number.PADDING.value:
                idx += 1
                continue

            if num == (Number.START_SEQUENCE.value):
                try:
                    is_negative, num, is_fraction, is_percent = \
                        numbers[idx+1], numbers[idx+2], numbers[idx+3], \
                        numbers[idx+4]
                except IndexError:
                    import pdb; pdb.set_trace()
                    pass
                if is_negative:
                    num = -num
                if is_fraction:
                    num = format(convert_whole_to_fraction(num), '.2f')
                else:
                    num = str(num)
                if is_percent:
                    num += '%'
                result.append(num)
                idx += 6  # TODO: this should be in NumberSequence?
                continue

            result.append(tokens[str(num)])
            idx += 1

        fn_parts = filename.split(os.sep)
        fn_prefix_index = fn_parts[-1].rfind('.')
        fn_prefix = fn_parts[-1][:fn_prefix_index]

        dir_name = os.path.join(os.sep.join(filename.split(os.sep)[:-1]),
                                'decoded')
        create_dirs([dir_name])

        out_filename = os.path.join(dir_name, fn_prefix + '.decoded')
        write_file(out_filename, ' '.join(result))


def remove_all_decoded_files():
    remove_files(cleaned_tags_dir(), '**', '*.decoded')


def decode_all_files(filenames, tokens_path):

    # remove_all_decoded_files()

    # num_dirs_to_process = 3
    # current_company_dir = ''

    # tokens, encoded_num_start_value_shift = read_tokens_file(tokens_path)
    tokens = read_tokens_file(tokens_path)

    for filename in filenames:

        # Ignore all files that don't have '.encoded' at the end
        if not filename.endswith('.encoded'):
            continue

        # filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2018-01-01_2018-12-31_10-K/tables-extracted/162.table-extracted.encoded'
        print(f'filename: {filename}')

        # company_dir_idx = len(cleaned_tags_dir())
        # company_dir = filename[company_dir_idx+1:].split(os.sep)[0]

        # if current_company_dir != company_dir:
        #     current_company_dir = company_dir
        #     num_dirs_to_process -= 1
        #     if num_dirs_to_process <= 0:
        #         break

        decode_file(filename, tokens)
        # break


def decode_training_files():
    paths = [os.path.join(generated_data_dir(), 'html',
                          'encoded', '*.encoded'),
             os.path.join(generated_data_dir(), 'expected_json',
                          'encoded', '*.encoded')]
    tokens_path = os.path.join(generated_data_dir(), 'tokens')
    decode_all_files(get_filenames(paths), tokens_path)


def decode_validation_test_files():
    paths = os.path.join(cleaned_tags_dir(),
                         '*', '10-k', '*', '*', '*.encoded')
    tokens_path = os.path.join(cleaned_tags_dir(), 'tokens')
    decode_all_files(get_filenames(paths), tokens_path)


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Usage: python decode.py encoded_filename')

    filename = sys.argv[1]
    # tokens, encoded_num_start_value_shift = read_tokens_file(tokens_file())
    tokens = read_tokens_file(tokens_file())
    decode_file(filename, tokens)
