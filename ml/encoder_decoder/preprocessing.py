import os
import re
import json
from generate.generate import generate_input, randomize_string
from utils.text import split_using_punctuation
from bs4 import BeautifulSoup, NavigableString
from utils.html import get_attr_names_values
# from utils.environ import extracted_tables_dir, generated_data_dir

regex_words = re.compile(
    r'header|table_number_interpretation|table_years_months|'
    r'table_data|name|sections|values|'
    r'end\_[a-z]+|'
    r'\b[a-zA-Z0-9]*\b|'
    '[\{\}\[\]\:\"\,]', re.MULTILINE)


def get_html_tokens(tag):
    token_seq = []

    if isinstance(tag, NavigableString):
        token_seq.append(str(tag.string).strip())
    else:
        token_seq.append(tag.name.strip())

        attr_names_values = []
        for name_or_value in get_attr_names_values(tag):
            for x in name_or_value.split():
                attr_names_values.extend(split_using_punctuation(x))

        for child in tag.children:
            token_seq.extend(get_html_tokens(child))
        token_seq.append('end_' + tag.name.strip())

    return token_seq


def get_json_tokens(json_text):

    token_seq = []
    matches = regex_words.findall(json_text)

    for match in matches:
        if len(match.strip()) == 0:
            continue

        token_seq.append(match)

    return token_seq


def tokenize_html_json(html_fn, json_fn):

    generated_input, json_expected = \
        generate_input(html_fn, 'unescaped', json_fn)

    # Now process those files to get the tokens
    top_tag = BeautifulSoup(generated_input, 'html.parser')
    html_tokens = get_html_tokens(top_tag)

    json_expected = json.dumps(json_expected)
    json_tokens = get_json_tokens(json_expected)

    print(f'html_token_len: {len(html_tokens)}, html_tokens: {html_tokens}\n\n')
    print(f'json_token_len: {len(json_tokens)}, json_tokens: {json_tokens}\n\n')

    return html_tokens, json_tokens


def tokenize():
    html_fn = '/Volumes/Seagate/generated-html-json/0001099932_centra_financial_holdings_inc__10-k__2008-01-01_2008-12-31_10-k__tables-extracted_split-tables__26.cleaned'
    json_fn = '/Volumes/Seagate/generated-html-json/0001099932_centra_financial_holdings_inc__10-k__2008-01-01_2008-12-31_10-k__tables-extracted_split-tables__26.json'

    randomized_html_tokens, randomized_json_tokens = \
        tokenize_html_json(html_fn, json_fn)
    # print(f'randomized_html_tokens: {randomized_html_tokens}\n\n')
    # print(f'randomized_json_tokens: {randomized_json_tokens}\n\n')
