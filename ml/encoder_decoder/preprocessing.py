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
                         r'[0-9\(\)\)\,\.\%]*|'
                         r'\b[a-zA-Z0-9]*\b|'
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


def tokenize_html():
    tokens = set()
    paths = [os.path.join(generated_data_dir(), 'html', '*.unescaped')]
    for filename in get_filenames(paths):
        tokens.update(tokenize_one_html_file(filename))
        print(f'len(tokens): {len(tokens)}, filename: {filename}')

    # Remove all length 0 tokens
    tokens = filter(lambda x: len(x) > 0, tokens)
    return list(tokens)


def tokenize_one_json_file(filename):
    text = read_file(filename)
    return get_json_tokens(text)


def tokenize_json():

    tokens = set()
    paths = [os.path.join(generated_data_dir(),
                          'expected_json', '*.expected_json')]
    for filename in get_filenames(paths):
        tokens.update(tokenize_one_json_file(filename))
        print(f'len(tokens): {len(tokens)}, filename: {filename}')

    # Remove all length 0 tokens
    tokens = filter(lambda x: len(x) > 0, tokens)
    return list(tokens)


def tokenize():
    tokens = tokenize_html()
    tokens.extend(tokenize_json())
    tokens_output_path = os.path.join(generated_data_dir(), 'tokens')
    write_json_to_file(tokens_output_path, tokens)
