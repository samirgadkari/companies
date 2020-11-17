'''
Takes HTML files from an input directory and replaces all text
and numbers with randomly-generated text and numbers
to create a new HTML file in the output directory.
'''
import os
import sys
import numpy as np
from bs4 import BeautifulSoup
from decouple import config
from ml.number import is_number
from utils.file import get_filenames, read_file, write_file, \
    get_json_from_file, write_json_to_file, copy_file, create_dirs
from utils.html import replace_names, replace_values, \
    make_html_strings_unique, is_unicode_em_dash, \
    convert_unicode_em_dash, YIELDED_STR, YIELDED_NUM, \
    strings_and_values_in_html, randomize_string
from utils.environ import text_samples_dir, generated_data_dir, \
    html_samples_dir, generated_html_json_dir
from ml.clean_tables import remove_comments

NUMBER_OF_OUTPUT_FILES = 20


class FilterItems():
    def __init__(self, items):
        self.items = items

    def apply(self, k, v):
        return k in self.items


def append_result_to_list(result, k, v):
    result.append(v)
    return result


def is_dict(v):
    return isinstance(v, dict)


def is_list(v):
    return isinstance(v, list)


def get(json_={}, result=[], filter_=None, output=[], recurse=True):
    if isinstance(json_, dict):
        for k, v in json_.items():
            if filter_(k, v):
                if (is_dict(v) or is_list(v)) and (recurse is True):
                    get(v, result, filter_, output, recurse)
                else:
                    result = output(result, k, v)
    elif isinstance(json_, list):
        for v in json_:
            if isinstance(v, str):
                result = output(result, None, v)
            elif is_dict(v) and (recurse is True):
                result = get(v, result, filter_, output, recurse)
            elif is_list(v) and (recurse is True):
                result = get(v, result, filter_, output, recurse)
    return result


def top_level_names(d):
    return \
        get(json_=d,
            result=[],
            filter_=FilterItems(['header']).apply,
            output=append_result_to_list)


def get_names(d):
    return \
        get(json_=d,
            result=[],
            filter_=FilterItems(['table_data', 'name', 'sections']).apply,
            output=append_result_to_list,
            recurse=True)


def get_values(d):
    return \
        get(json_=d,
            result=[],
            filter_=FilterItems(['table_data',
                                 'values', 'sections']).apply,
            output=append_result_to_list,
            recurse=True)


def all_elements_are_in_data(data, elements):
    results = [e in data for e in elements]
    for i, r in enumerate(results):
        if r is False:
            # print(f'data: {data}')
            print(f'Not found in data: {elements[i]}')
    return all(results)


def data_contains_all_elements(data, elements):
    return all_elements_are_in_data(data, get_names(elements)) and \
           all_elements_are_in_data(data, get_values(elements))


def check_hand_created_samples():
    result = True
    for samples_dir, input_name in \
        zip([text_samples_dir(), html_samples_dir()],
            ['text_input', 'html_input']):
        data_filenames = get_filenames(samples_dir, input_name, '*')
        json_filenames = get_filenames(samples_dir, 'json_input', '*')
        data_filenames = sorted(data_filenames)
        json_filenames = sorted(json_filenames)
        for d_fn, j_fn in zip(data_filenames, json_filenames):
            print(f'Checking:\n  {d_fn}\n  {j_fn}\n')
            input_data = read_file(d_fn)
            json_input_data = get_json_from_file(j_fn)

            if data_contains_all_elements(input_data,
                                          json_input_data) is False:
                print(f'Errors found in:\n  input: {d_fn}\n'
                      f'  json_input: {j_fn}')
                result = False
    return result


def update_expected_strings(json_, mappings):
    map_keys = list(mappings.keys())
    if isinstance(json_, dict):
        new_dict = {}
        for k, v in json_.items():
            if isinstance(v, list):
                new_dict[k] = update_expected_strings(v, mappings)
            elif v in map_keys:
                new_dict[k] = mappings[v]
            else:
                new_dict[k] = v
        return new_dict
    elif isinstance(json_, list):
        new_list = []
        for v in json_:
            if isinstance(v, list):
                new_list.append(update_expected_strings(v, mappings))
            elif isinstance(v, dict):
                new_list.append(update_expected_strings(v, mappings))
            elif v in map_keys:
                new_list.append(mappings[v])
            else:
                new_list.append(v)
        return new_list
    raise ValueError('Unexpected type in JSON dictionary')


def numeric_tokens(h_tokens):
    return list(map(lambda x: x[1], h_tokens))


def check_missing_tokens(h_tokens, j_tokens):

    # HTML tokens contain tuples (number value text, cleaned number value text).
    # We select just the cleaned number value text here and compare it to the
    # cleaned JSON number tokens.
    h_tokens = numeric_tokens(h_tokens)

    html_tokens = set(h_tokens)
    json_tokens = set(j_tokens)
    html_minus_json_len = len(html_tokens - json_tokens)
    json_minus_html_len = len(json_tokens - html_tokens)
    assert(html_minus_json_len == 0 and json_minus_html_len == 0)

    # if html_minus_json_len > json_minus_html_len:
    #     print(f'set(HTML) - set(JSON): {html_tokens - json_tokens}\n\n')
    # else:
    #     print(f'set(JSON) - set(HTML): {json_tokens - html_tokens}\n\n')

    # print(f'h_tokens: {h_tokens}\n\n')
    # print(f'j_tokens: {j_tokens}')


def generate_input(input_fn, fn_type, json_input_fn):

    def separate_values_strings(top_tag):
        filter_str = lambda x: True if x[0] == YIELDED_STR else False
        map_str = lambda x: (x[1], x[2])
        filter_value = lambda x: True if x[0] == YIELDED_NUM else False
        map_value = lambda x: (x[1], x[2])

        def extract_tag_str(html_strings_tags_values, filter_fn, map_fn):
            temp = filter(filter_fn, html_strings_tags_values)
            return list(map(map_fn, temp))

        html_strings_tags_values = list(strings_and_values_in_html(top_tag))
        html_tags_strings = extract_tag_str(html_strings_tags_values,
                                            filter_str, map_str)

        html_tags_values = extract_tag_str(html_strings_tags_values,
                                        filter_value, map_value)
        return html_tags_strings, html_tags_values

    if fn_type != 'unescaped':
        raise ValueError(f'We are only supporting HTML at this point - '
                         f'not {fn_type}')

    input_data = read_file(input_fn)
    top_tag = BeautifulSoup(input_data, 'html.parser')
    remove_comments(top_tag)
    html_tags_strings, html_tags_values = separate_values_strings(top_tag)

    json_input = get_json_from_file(json_input_fn)

    json_names = top_level_names(json_input)
    json_names.extend(get_names(json_input))

    mappings = {}  # original string to new string
    for json_name in json_names:
        mappings[json_name] = randomize_string(json_name)

    json_values = list(get_values(json_input))

    json_values = \
        list(filter(lambda x: True if is_number(x) else False, json_values))

    replace_names(json_names, html_tags_strings, mappings)

    # print(f'mappings: {mappings}\n\n')

    value_mappings = \
        {value: randomize_string(value)
         for value in json_values}
    mappings.update(value_mappings)
    mappings['-'] = '999999999'

    # print(f'mappings: {mappings}')
    # check_missing_tokens(html_tags_values, json_values)
    number_tokens = list(numeric_tokens(html_tags_values))
    for token in number_tokens:
        mappings[token] = randomize_string(token)

    replace_values(json_values, html_tags_values, mappings)

    json_expected = update_expected_strings(json_input, mappings)

    return str(top_tag), json_expected


def generate_random_text(input_filenames, num_output_files):
    print('Getting set of all chars in data', end='')
    print(' ... done')

    for id in range(num_output_files):
        input_fn = np.random.choice(input_filenames)
        # input_fn = '/Volumes/datadrive/generated-html-json/0001035713_providian_financial_corp__10-k__2004-01-01_2004-12-31_10-k__tables-extracted_split-tables__24.unescaped'

        # To be done again as some of the numbers that should be empty are 9's,
        # even in the html page.
        print('{:6d}: file: {}'.format(id, input_fn))

        fn_parts = input_fn.split(os.sep)
        fn_name = fn_parts[-1].split('.')
        fn_prefix, fn_type = fn_name[0], fn_name[1]

        json_input_fn = os.sep + os.path.join(*fn_parts[:-1],
                                              fn_prefix + '.json')
        json_generated_output_fn = os.path.join(generated_data_dir(),
                                                'html',
                                                str(id) + '.' + fn_type)
        json_expected_output_fn = os.path.join(generated_data_dir(),
                                               'expected_json',
                                               str(id) + '.expected_json')

        input_generated_fn = os.path.join(generated_data_dir(),
                                          'input',
                                          str(id) + '.input')

        generated_input, json_expected = \
            generate_input(input_fn,
                           fn_type,
                           json_input_fn)

        write_file(json_generated_output_fn, generated_input)
        write_json_to_file(json_expected_output_fn, json_expected)
        copy_file(input_fn, input_generated_fn)

        # break


def generate_samples():

    create_dirs([os.path.join(generated_data_dir(), 'html'),
                 os.path.join(generated_data_dir(), 'expected_json'),
                 os.path.join(generated_data_dir(), 'input')])

    data_filenames = []
    for samples_dir in [generated_html_json_dir()]:
        sorted_files = sorted(list(get_filenames([os.path.join(samples_dir, '*')])))
        sorted_files = list(filter(lambda x: x.endswith('unescaped'),
                                   sorted_files))
        data_filenames.extend(sorted_files)

    generate_random_text(data_filenames, NUMBER_OF_OUTPUT_FILES)


if __name__ == '__main__':
    if check_hand_created_samples() is True:
        print('Samples are good')
    else:
        print('Some samples are bad')
        sys.exit(-1)

    generate_samples()
