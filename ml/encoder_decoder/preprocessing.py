import os
import re
from utils.text import split_using_punctuation
from bs4 import BeautifulSoup, NavigableString
from utils.html import get_attr_names_values
from utils.file import read_file, get_filenames, write_json_to_file
from utils.environ import extracted_tables_dir, generated_data_dir

regex_words = re.compile(r'"header"|'
                         r'"table_number_interpretation"|'
                         r'"table_years_months"|'
                         r'"table_data"|'
                         r'"name"|'
                         r'"sections"|'
                         r'"values"|'
                         r'[0-zA-Z-9\(\)\)\,\.\%\ ]*|'
                         r'[\{\}\[\]\:\"\,]', re.MULTILINE)


def get_html_tokens(tag):
    token_seq = []

    if isinstance(tag, NavigableString):
        token_seq.append(str(tag.string).strip().lower())
    else:
        token_seq.append(tag.name.strip().lower())

        attr_names_values = []
        for name_or_value in get_attr_names_values(tag):
            for x in name_or_value.split():
                attr_names_values.extend(split_using_punctuation(x))

        for child in tag.children:
            token_seq.extend(get_html_tokens(child))
        token_seq.append('end_' + tag.name.strip().lower())

    return token_seq


def get_json_tokens(json_text):

    token_seq = []
    matches = regex_words.findall(json_text)

    for match in matches:
        if len(match.strip()) == 0:
            continue

        token_seq.append(match)

    return token_seq


def tokenize_one_html_file(filename):
    text = read_file(filename)
    top_tag = BeautifulSoup(text, 'html.parser')
    return get_html_tokens(top_tag)


def tokenize_one_json_file(filename):
    text = read_file(filename)
    return get_json_tokens(text)


def tokenize_html():
    filename = os.path.join(generated_data_dir(), 'html', '0.unescaped')
    print(tokenize_one_html_file(filename))


def tokenize_json():
    filename = os.path.join(generated_data_dir(),
                            'expected_json', '0.expected_json')
    print(tokenize_one_json_file(filename))
