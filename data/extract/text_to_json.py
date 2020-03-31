import os
import re
import sys
import html
import glob
import json
import numpy as np
from decouple import config

text_samples_dir = config('TEXT_SAMPLES_DIR')
html_samples_dir = config('HTML_SAMPLES_DIR')
generated_samples_dir = config('GENERATED_SAMPLES_DIR')

def read_file(fn):
    with open(fn, 'r') as f:
        return f.read()

def write_file(fn, data):
    with open(fn, 'w') as f:
        f.write(data)

def copy_file(src, dst):
    write_file(dst, read_file(src))

def get_json_from_file(fn):
    with open(fn, 'r') as f:
        return json.load(f)

def write_json_to_file(fn, data):
    with open(fn, 'w') as f:
        s = json.dumps(data, indent=4)
        f.write(s)

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

# TODO: This is too dense - need to clean it up !!
def get(json_={}, result=[], filter_=None, output=[], recurse=True):
    if isinstance(json_, dict):
        for k, v in json_.items():
            if filter_(k, v):
                if (is_dict(v) or is_list(v)) and (recurse == True):
                    get(v, result, filter_, output, recurse)
                else:
                    result = output(result, k, v)
    elif isinstance(json_, list):
        for v in json_:
            if isinstance(v, str):
                result = output(result, None, v)
            elif is_dict(v) and (recurse == True):
                result = get(v, result, filter_, output, recurse)
            elif is_list(v) and (recurse == True):
                result = get(v, result, filter_, output, recurse)
    return result

def top_level_names(d):
    return \
        get(json_=d,
            result=[],
            filter_= \
                FilterItems( \
                    ['table_number_interpretation', 'table_years',
                     'table_months', 'table_years_months', 'name']).apply,
            output=append_result_to_list)

def get_names(d):
    return \
        get(json_=d,
            result=[],
            filter_= FilterItems(['table_data', 'name', 'sections']).apply,
            output=append_result_to_list,
            recurse=True)

def get_values(d):
    return \
        get(json_=d,
            result=[],
            filter_= FilterItems(['table_data', 'values', 'sections']).apply,
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
        zip([text_samples_dir, html_samples_dir],
            ['text_input', 'html_input']):
        data_filenames = glob.iglob(os.path.join(samples_dir,
                                                 input_name,
                                                 '*'))
        json_filenames = glob.iglob(os.path.join(samples_dir,
                                                 'json_input',
                                                 '*'))
        data_filenames = sorted(data_filenames)
        json_filenames = sorted(json_filenames)
        for d_fn, j_fn in zip(data_filenames, json_filenames):
            print(f'Checking:\n  {d_fn}\n  {j_fn}\n')
            input_data = read_file(d_fn)
            json_input_data = get_json_from_file(j_fn)

            if data_contains_all_elements(input_data,
                                          json_input_data) == False:
                print(f'Errors found in:\n  input: {d_fn}\n'
                      f'  json_input: {j_fn}')
                result = False
    return result

def set_of_all_chars_in_data():
    all_chars = set()
    for input_dirname in [text_samples_dir, html_samples_dir]:
        json_filenames = glob.iglob(os.path.join(input_dirname,
                                                 'json_input',
                                                 '*'))
        for fn in json_filenames:
            json_table = get_json_from_file(fn)
            names = get_names(json_table)
            for name in names:
                all_chars.update(list(name))
            values = get_values(json_table)
            for value in values:
                all_chars.update(list(value))

    return list(all_chars)

def randomize_string(s, all_chars):
    return ''.join(np.random.choice(all_chars, len(s)))

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


def replace_value_in_html(input_data, value, updated_str):
    pos = 0
    while True:
        idx = input_data[pos:].find(value)
        if idx == -1:
            break;
        pos = pos + idx
        if (input_data[pos-2] == '&') and \
            (input_data[pos-1] == '#'):
            pos = pos + 5  # This will get us beyond this part of the value
        else:
            return input_data[:pos] + \
                   input_data[pos:].replace(value, updated_str, 1)
    raise ValueError(f'Could not find {value} in file')

def generate_input(input_fn, fn_type, json_input_fn, all_chars):
    input_data = read_file(input_fn)

    json_input = get_json_from_file(json_input_fn)
    mappings = {}  # original string to new string
    for name in top_level_names(json_input):
        updated_str = randomize_string(name, all_chars)
        mappings[name] = updated_str
        input_data = input_data.replace(name, updated_str, 1)
    for name in get_names(json_input):
        updated_str = randomize_string(name, all_chars)
        mappings[name] = updated_str
        input_data = input_data.replace(name, updated_str, 1)
    for value in get_values(json_input):
        updated_str = randomize_string(value, all_chars)
        mappings[value] = updated_str
        if fn_type == 'html':

            input_data = replace_value_in_html(input_data,
                                               value,
                                               updated_str)
        else:
            input_data = input_data.replace(value, updated_str, 1)

    json_expected = update_expected_strings(json_input, mappings)
    return input_data, json_expected

def generate_random_text(input_filenames, num_output_files):
    print('Getting set of all chars in data', end='')
    all_chars = set_of_all_chars_in_data()
    print(' ... done')
    print(f'all_chars: {all_chars}')

    for id in range(num_output_files):
        input_fn = np.random.choice(input_filenames)

        fn_parts = input_fn.split(os.sep)
        fn_name = fn_parts[-1].split('.')
        fn_prefix, fn_type = fn_name[0], fn_name[1]

        json_input_fn = os.path.join(*fn_parts[:-2],
                                     'json_input',
                                     fn_prefix + '.json')
        json_generated_output_fn = os.path.join(generated_samples_dir,
                                                str(id) + '.' + fn_type)
        json_expected_output_fn = os.path.join(generated_samples_dir,
                                               str(id) + '.expected_json')

        input_generated_fn = os.path.join(generated_samples_dir,
                                          str(id) + '.input')
        generated_input, json_expected = generate_input(input_fn,
                                                        fn_type,
                                                        json_input_fn,
                                                        all_chars)
        write_file(json_generated_output_fn, generated_input)
        write_json_to_file(json_expected_output_fn, json_expected)
        copy_file(input_fn, input_generated_fn)

def generate_samples():
    data_filenames = []
    for samples_dir, input_name in \
        zip([text_samples_dir, html_samples_dir],
            ['text_input', 'html_input']):
        sorted_files = sorted(list(glob.iglob(os.path.join(samples_dir,
                                                           input_name,
                                                           '*'))))
        data_filenames.extend(sorted_files)

    generate_random_text(data_filenames, 10)


if __name__ == '__main__':
    if check_hand_created_samples() == True:
        print('Samples are good')
    else:
        print('Some samples are bad')
        sys.exit(-1)

    generate_samples()
