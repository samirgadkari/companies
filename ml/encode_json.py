import re
import os
from ml.number import is_number, get_number, number_to_sequence, Number
from ml.encode_common import update_seq_and_number_dict, convert_dict_values, \
    encode_file
from utils.file import write_json_to_file

regex_words = re.compile(r'"header"|'
                         r'"table_number_interpretation"|'
                         r'"table_years_months"|'
                         r'"table_data"|'
                         r'"name"|'
                         r'"sections"|'
                         r'"values"|'
                         r'[0-9\(\)\)\,\.\%]*|'
                         r'\b[a-zA-Z0-9]*\b|'
                         r'[\{\}\[\]\:\"\,]', re.MULTILINE)


def get_json_sequences(out_dirname, filename, json_text,
                       write_number_dict=True):
    token_seq = []
    word_num = Number.START_WORD_NUM.value
    number_dict = {}
    reverse_number_dict = {}

    matches = regex_words.findall(json_text)
    words = []

    for match in matches:
        if len(match.strip()) == 0:
            continue

        if is_number(match):
            is_negative, num_seq, is_percent = get_number(match)

            if num_seq is not False:
                words.append(number_to_sequence(is_negative,
                                                num_seq,
                                                is_percent))
            else:
                raise ValueError(f'match: {match} is not a number')
        else:
            words.append(match)

    word_num = update_seq_and_number_dict(words, token_seq,
                                          word_num, number_dict,
                                          reverse_number_dict)

    if write_number_dict is True:
        write_json_to_file(os.path.join(out_dirname,
                                        filename.split(os.sep)[-1] + '.nums'),
                           convert_dict_values(number_dict))
    return token_seq, number_dict


def find_json_encodings(out_dirname, filename, json_text, tokens):
    token_seq, _ = get_json_sequences(out_dirname, filename, json_text,
                                      write_number_dict=True)
    tokens.update(token_seq)


def encode_json(out_dirname, filename, json_text, tokens):
    token_seq, number_dict = \
        get_json_sequences(out_dirname, filename, json_text,
                           write_number_dict=False)
    return encode_file(out_dirname, filename, token_seq, tokens, number_dict)
