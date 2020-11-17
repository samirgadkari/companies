import os
import re
import json
import numpy as np
from generate.generate import generate_input, randomize_string
from utils.text import split_using_punctuation
from bs4 import BeautifulSoup, NavigableString
from utils.html import get_attr_names_values
from utils.file import get_filenames, read_file, write_file, create_dirs, \
    write_json_to_file
from utils.environ import generated_data_dir, generated_html_json_dir
# from utils.environ import extracted_tables_dir, generated_data_dir

regex_words = re.compile(
    r'header|table_number_interpretation|table_years_months|'
    r'table_data|name|sections|values|'
    r'end\_[a-z0-9]+|'
    r'\b[a-zA-Z0-9]*\b|'
    r'[\{\}\[\]\:\"\,]', re.MULTILINE)

# Generate files with randomized text values if True,
# If False, the files we're using are already randomized.
generate = False
NUMBER_OF_OUTPUTS = 20  # Randomly sample input files to generate
                        # this number of output strings.


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
    # You should only call generate on the original files,
    # not on the files that have randomized strings. If we do,
    # the generate code cannot tell if an string is a number (value),
    # and which string is just a string.
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

    def update_max_token_len(html, json, max_len):
        html_len, json_len = len(html.split()), len(json.split())
        return max(html_len, max(json_len, max_len))

    output_path = os.path.join(generated_data_dir())
    if generate is True:
        input_fns = list(get_filenames([os.path.join(generated_html_json_dir(),
                                                    '*.unescaped')]))
        html_fns, json_fns = [], []
        for id in range(NUMBER_OF_OUTPUTS):
            html_fn = np.random.choice(input_fns)

            fn_parts = html_fn.split(os.sep)
            fn_name = fn_parts[-1].split('.')
            fn_prefix, fn_type = fn_name[0], fn_name[1]

            json_fn = os.sep + os.path.join(*fn_parts[:-1],
                                            fn_prefix + '.json')
            html_fns.append(html_fn)
            json_fns.append(json_fn)

        combined_fns = zip(html_fns, json_fns)
    else:
        combined_fns = zip(
            list(get_filenames([os.path.join(output_path,
                                             'html',
                                             '*.unescaped')])),
            list(get_filenames([os.path.join(output_path,
                                             'expected_json',
                                             '*.expected_json')])))

    # print(f'combined_fns: {(list(combined_fns))[:2]}')

    combined_tokens = []
    tokens = set()
    max_token_len = 0
    for html_fn, json_fn in combined_fns:
        # html_fn = '/Volumes/Seagate/generated-data/html/0.unescaped'
        # json_fn = '/Volumes/Seagate/generated-data/expected_json/0.expected_json'

        print(f'html_fn: {html_fn}')
        print(f'json_fn: {json_fn}')
        html_tokens, json_tokens = tokenize_html_json(html_fn, json_fn, generate=generate)
        html_tokens = ' '.join(html_tokens).replace("'", "")

        json_tokens = ' '.join(json_tokens).replace("'", "")
        # Remove json string's quotes at the beginning and end
        json_tokens = json_tokens[2:len(json_tokens) - 2]

        max_token_len = update_max_token_len(html_tokens, json_tokens,
                                             max_token_len)

        tokens.update(html_tokens.split())
        tokens.update(json_tokens.split())

        combined_tokens.append(html_fn + '^' + html_tokens + \
            '^' + json_fn + '^' + json_tokens)

    write_file(os.path.join(output_path, 'tokenized'),
               '\n'.join(combined_tokens))

    tokens = sorted(list(tokens))
    tokens.reverse()
    tokens.extend(['<sos>', '<pad>', '<eos>'])
    tokens.reverse()

    write_json_to_file(os.path.join(output_path, 'tokens'), tokens)

    with open(os.path.join(output_path, 'max_token_len'), 'w') as f:
        f.write(f'max_token_len: {max_token_len}')

if __name__ == '__main__':
    tokenize_training_set()
