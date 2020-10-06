import os
from bs4 import BeautifulSoup, NavigableString
from utils.html import get_attr_names_values
from utils.file import write_json_to_file
from utils.text import split_using_punctuation
from ml.number import number_to_sequence, get_number, Number
from ml.encode_common import convert_dict_values, update_seq_and_number_dict, \
    encode_file


def get_html_sequences(out_dirname, filename, top_tag,
                       write_number_dict=True):
    token_seq = []
    word_num = Number.START_WORD_NUM.value
    number_dict = {}
    reverse_number_dict = {}

    def recurse(tag):
        nonlocal token_seq, word_num

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
                is_negative, num_seq, is_percent = get_number(word)
                if num_seq is not False:
                    # We must append the tuple here.
                    # If we extend, each value in the tuple will be
                    # separately appended and we will lose the
                    # tuple.
                    words.append(number_to_sequence(is_negative,
                                                    num_seq,
                                                    is_percent))
                else:
                    for x in split_using_punctuation(word):
                        words.append(x)
            word_num = update_seq_and_number_dict(words, token_seq,
                                                  word_num, number_dict,
                                                  reverse_number_dict)
        else:
            token_seq.append(tag.name.strip().lower())

            attr_names_values = []
            for name_or_value in get_attr_names_values(tag):
                for x in name_or_value.split():
                    attr_names_values.extend(split_using_punctuation(x))

            word_num = update_seq_and_number_dict(attr_names_values, token_seq,
                                                  word_num, number_dict,
                                                  reverse_number_dict)
            for child in tag.children:
                recurse(child)
            token_seq.append('end_' + tag.name.strip().lower())

        return word_num

    recurse(top_tag)

    if write_number_dict is True:
        write_json_to_file(os.path.join(out_dirname,
                                        filename.split(os.sep)[-1] + '.nums'),
                           convert_dict_values(number_dict))
    return token_seq, number_dict


def find_html_table_encodings(out_dirname, filename, table_text, tokens):
    soup = BeautifulSoup(table_text, 'html.parser')
    file_token_seq, _ = get_html_sequences(out_dirname, filename, soup,
                                           write_number_dict=True)
    tokens.update(file_token_seq)


def encode_html_table(out_dirname, filename, table_text, tokens):

    soup = BeautifulSoup(table_text, 'html.parser')
    token_seq, number_dict = get_html_sequences(out_dirname, filename, soup,
                                                write_number_dict=False)
    return encode_file(out_dirname, filename, token_seq, tokens, number_dict)
