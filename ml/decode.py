import os
import sys
from utils.environ import tokens_file, cleaned_tags_dir
from ml.tokens import read_tokens_file
from ml.number import Number
from utils.file import write_file, remove_files, \
    get_filenames, file_exists


def decode_file(filename, tokens):
    num_seq_offset = len(tokens)

    with open(filename, 'r') as f:
        numbers = list(map(int, f.read().split()))

        result = []
        idx = 0
        while(idx < len(numbers)):

            num = numbers[idx]
            if num == Number.PADDING.value:
                idx += 1
                continue

            if num == Number.START_SEQUENCE.value:
                is_negative, num, is_percent = \
                    numbers[idx+1], numbers[idx+2], numbers[idx+3]
                num -= num_seq_offset
                if is_negative:
                    num = str(-num)
                else:
                    num = str(num)
                if is_percent:
                    num += '%'
                result.append(num)
                idx += 5  # TODO: this should be in NumberSequence?
                continue

            result.append(tokens[str(num)])
            idx += 1

        out_filename = filename[:filename.rfind('.')] + '.decoded'
        write_file(out_filename, ' '.join(result))


def remove_all_decoded_files():
    remove_files(cleaned_tags_dir(), '**', '*.decoded')


def decode_all_files():

    remove_all_decoded_files()

    num_dirs_to_process = 3
    current_company_dir = ''

    tokens = read_tokens_file(tokens_file())

    for filename in get_filenames(cleaned_tags_dir(),
                                  '*', '10-k', '*', '*', '*'):
        # Ignore output files
        if filename.endswith('.decoded'):
            continue

        # Ignore files that are already processed
        if file_exists(filename + '.decoded'):
            continue

        # Ignore all files that don't have '.encoded' at the end
        if not filename.endswith('.encoded'):
            continue

        # filename = '/Volumes/datadrive/tags-cleaned/0000707605_AMERISERV_FINANCIAL_INC__PA_/10-k/2018-01-01_2018-12-31_10-K/tables-extracted/162.table-extracted.encoded'
        print(f'filename: {filename}')

        company_dir_idx = len(cleaned_tags_dir())
        company_dir = filename[company_dir_idx+1:].split(os.sep)[0]

        if current_company_dir != company_dir:
            current_company_dir = company_dir
            num_dirs_to_process -= 1
            if num_dirs_to_process <= 0:
                break

        decode_file(filename, tokens)
        # break


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Usage: python decode.py encoded_filename')

    filename = sys.argv[1]
    tokens = read_tokens_file(tokens_file())
    decode_file(filename, tokens)
