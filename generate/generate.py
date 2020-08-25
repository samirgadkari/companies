import os
import sys
import numpy as np
import string
from decouple import config
from utils.file import get_filenames, read_file, write_file, \
    get_json_from_file, write_json_to_file, copy_file
from utils.html import replace_names, replace_values, \
    make_html_strings_unique

text_samples_dir = config('TEXT_SAMPLES_DIR')
html_samples_dir = config('HTML_SAMPLES_DIR')
generated_samples_dir = config('GENERATED_SAMPLES_DIR')

# If the length of the data is more than this size,
# we pick a length between this length and the actual
# data size length. If it is less, then we pick
# the length of the actual data size.
# Using the selected length, we generate random data
# of that length.
MIN_DATA_SIZE = 5


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
            filter_=FilterItems(
                ['table_number_interpretation', 'table_years',
                 'table_months', 'table_years_months', 'name']).apply,
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
            filter_=FilterItems(['table_data', 'values', 'sections']).apply,
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


def set_of_all_chars_in_data():
    # all_chars = set()
    # for input_dirname in [text_samples_dir, html_samples_dir]:
    #     json_filenames = get_filenames(input_dirname, 'json_input', '*')
    #     for fn in json_filenames:
    #         json_table = get_json_from_file(fn)
    #         names = get_names(json_table)
    #         for name in names:
    #             all_chars.update(list(name))
    #         values = get_values(json_table)
    #         for value in values:
    #             all_chars.update(list(value))
    all_chars = list(string.ascii_lowercase)
    all_chars.extend(string.ascii_uppercase)
    all_chars.extend(string.digits)
    all_chars.append(' ')

    # We convert it to a set first to ensure that there are no
    # duplicate characters
    return list(set(all_chars))


def randomize_string(s, all_chars, mappings):
    # We want to have separate mappings for even the same value
    # which was found in multiple places. This makes it a guarantee
    # that we will map to the correct location in the JSON file.
    # if s in mappings:
    #     return mappings[s]

    if len(s) > MIN_DATA_SIZE:
        length = np.random.randint(MIN_DATA_SIZE, len(s) + 1)
    else:
        length = MIN_DATA_SIZE
    return ''.join(np.random.choice(all_chars, length))


def randomize_number(num, all_chars, mappings):
    s = randomize_string(num, all_chars, mappings)
    is_negative, is_fraction = np.random.choice([True, False], 2)

    if is_negative & is_fraction:
        return '(' + s[:2] + '.' + s[2:] + ')'
    elif is_negative:
        return '(' + s + ')'
    elif is_fraction:
        return s[:2] + '.' + s[2:]
    else:
        # This removes any perceding zeros for the number.
        return str(int(s))


def update_expected_strings(json_, mappings):
    map_keys = list(mappings.keys())
    # if isinstance(json_, list):
    #     import pdb; pdb.set_trace()
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


def generate_input(input_fn, fn_type, json_input_fn, all_chars):
    input_data = read_file(input_fn)
    # input_data = replace_named_or_numeric(input_data)

    json_input = get_json_from_file(json_input_fn)

    # If the names in the JSON document are not unique,
    # make them unique. This way, the generated output
    # HTML document has unique names and we can see
    # that we get the right name at the right location
    # after we have encoded and decoded it.
    names = get_names(json_input)
    len_names = len(names)
    len_set_names = len(set(names))
    if len_names != len_set_names:
        input_data, names = \
            make_html_strings_unique(input_data, names)

    all_names = top_level_names(json_input)
    all_names.extend(names)

    mappings = {}  # original string to new string
    for name in all_names:
        mappings[name] = randomize_string(name, all_chars, mappings)

    input_data = replace_names(input_data, mappings)

    if fn_type == 'html':
        json_values = list(get_values(json_input))
        # For values, we only need to replace numbers.
        all_chars = list(string.digits)
        updated_strings = [randomize_number(value, all_chars, mappings)
                           for value in json_values]
        input_data, json_mappings = \
            replace_values(input_data, json_values, updated_strings)
        mappings.update(json_mappings)
    else:
        raise ValueError('We are only supporting HTML at this point - '
                         'not {fn_type}')

    json_expected = update_expected_strings(json_input, mappings)
    return input_data, json_expected


def generate_random_text(input_filenames, num_output_files):
    print('Getting set of all chars in data', end='')
    all_chars = set_of_all_chars_in_data()
    print(' ... done')
    print(f'all_chars: {all_chars}')

    for id in range(num_output_files):
        input_fn = np.random.choice(input_filenames)
        # input_fn = './data/extract/samples/html/html_input/2.html'
        print(f'input_fn: {input_fn}')

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
        generated_input, json_expected = \
            generate_input(input_fn,
                           fn_type,
                           json_input_fn,
                           all_chars)

        write_file(json_generated_output_fn, generated_input)
        write_json_to_file(json_expected_output_fn, json_expected)
        copy_file(input_fn, input_generated_fn)


def generate_samples():
    data_filenames = []
    for samples_dir, input_name in \
        zip([html_samples_dir],
            ['html_input']):
        sorted_files = sorted(list(get_filenames(samples_dir,
                                                 input_name, '*')))
        data_filenames.extend(sorted_files)

    generate_random_text(data_filenames, 10)


if __name__ == '__main__':
    if check_hand_created_samples() is True:
        print('Samples are good')
    else:
        print('Some samples are bad')
        sys.exit(-1)

    generate_samples()
