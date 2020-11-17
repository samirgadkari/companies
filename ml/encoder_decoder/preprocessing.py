import os
import re
import json
from generate.generate import generate_input, randomize_string
from utils.text import split_using_punctuation
from bs4 import BeautifulSoup, NavigableString
from utils.html import get_attr_names_values
from utils.file import get_filenames, read_file, write_file, create_dirs
from utils.environ import generated_data_dir
# from utils.environ import extracted_tables_dir, generated_data_dir

regex_words = re.compile(
    r'header|table_number_interpretation|table_years_months|'
    r'table_data|name|sections|values|'
    r'end\_[a-z]+|'
    r'\b[a-zA-Z0-9]*\b|'
    r'[\{\}\[\]\:\"\,]', re.MULTILINE)


def get_html_tokens(tag):
    token_seq = []

    if isinstance(tag, NavigableString):
        token_seq.append(str(tag.string).strip())
    else:
        tag_name = tag.name.strip()
        if '[' in tag_name and ']' in tag_name:
            tag_name = tag_name.replace('[', '').replace(']', '')

        token_seq.append(tag_name)

        attr_names_values = []
        for name_or_value in get_attr_names_values(tag):
            for x in name_or_value.split():
                attr_names_values.extend(split_using_punctuation(x))
                # print(f'x: {x} split x: {split_using_punctuation(x)}')
        token_seq.extend(attr_names_values)

        for child in tag.children:
            token_seq.extend(get_html_tokens(child))
        token_seq.append('end_' + tag_name)

    return token_seq


def get_json_tokens(json_text):

    token_seq = []
    matches = regex_words.findall(json_text)

    for match in matches:
        if len(match.strip()) == 0:
            continue

        token_seq.append(match)

    return token_seq


def tokenize_html_json(html_fn, json_fn, generate=False):

    # Very likely that we don't need to call generate,
    # but it is here if required.
    if generate is True:
        html_data, json_data = \
            generate_input(html_fn, 'unescaped', json_fn)
    else:
        html_data = read_file(html_fn).replace('\n', '')
        json_data = read_file(json_fn).replace('\n', '')

    # Now process those files to get the tokens
    top_tag = BeautifulSoup(html_data, 'html.parser')
    html_tokens = get_html_tokens(top_tag)

    json_expected = json.dumps(json_data)
    json_tokens = get_json_tokens(json_expected)

    return html_tokens, json_tokens


def tokenize_training_set():

    base_path = os.path.join(generated_data_dir())

    combined_fns = zip(list(get_filenames([os.path.join(base_path,
                                                        'html', '*.unescaped')])),
                       list(get_filenames([os.path.join(base_path,
                                                       'expected_json',
                                                        '*.expected_json')])))

    # print(f'combined_fns: {(list(combined_fns))[:2]}')

    for html_fn, json_fn in combined_fns:
        # html_fn = '/Volumes/Seagate/generated-data/html/0.unescaped'
        # json_fn = '/Volumes/Seagate/generated-data/expected_json/0.expected_json'

        print(f'html_fn: {html_fn}')
        print(f'json_fn: {json_fn}')
        html_tokens, json_tokens = tokenize_html_json(html_fn, json_fn)
        html_tokens = ' '.join(html_tokens).replace("'", "")
        json_tokens = ' '.join(json_tokens).replace("'", "")

        fn = html_fn.split(os.sep)[-1].split('.')[0] + '.tokenized'
        write_file(os.path.join(out_dirname_html, fn), html_tokens)
        fn = json_fn.split(os.sep)[-1].split('.')[0] + '.tokenized'
        write_file(os.path.join(out_dirname_json, fn), json_tokens)

        # print(f'randomized_html_tokens: {html_tokens}\n\n')
        # print(f'randomized_json_tokens: {json_tokens}\n\n')


if __name__ == '__main__':
    tokenize_training_set()
