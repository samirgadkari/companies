import os
import glob
import json
import numpy as np
from decouple import config

text_samples_dir = config('TEXT_SAMPLES_DIR')
html_samples_dir = config('HTML_SAMPLES_DIR')


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
                    ['table_number_interpretation', 'table_years', 'table_months', 'name']).apply,
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

def all_elements_are_in_data(elements, data):
    results = [e in data for e in elements]
    for i, r in enumerate(results):
        if r is False:
            print(f'{elements[i]}: not found in data')
    return all(results)

def data_contains_all_elements(data, elements):
    return all_elements_are_in_data(get_names(elements), data) and \
           all_elements_are_in_data(get_values(elements), data)

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
        for d_fn, j_fn in zip(data_filenames, json_filenames):
            print(f'Checking:\n  {d_fn}\n  {j_fn}\n')
            with open(d_fn, 'r') as f:
                input_data = f.read()
            with open(j_fn, 'r') as f:
                json_input_data = json.load(f)
            if data_contains_all_elements(input_data,
                                          json_input_data) == False:
                print(f'Errors found in:\n  input: {d_fn}\n'
                      f'  json_input: {j_fn}')
                result = False
    return result

with open('./extract_data/samples/text/text_input/1.text', 'r') as f:
    data = f.read()

with open('./extract_data/samples/text/json_input/1.json', 'r') as f:
    j = json.load(f)

with open('./extract_data/samples/html/html_input/1.html', 'r') as f:
    data = f.read()

with open('./extract_data/samples/html/json_input/1.json', 'r') as f:
    j = json.load(f)

# def generate_random_text(input_text_filenames, num_output_files):
#     for _ in range(num_output_files):
#         input_text_fn = np.random.choice(input_text_filenames)

#         fn_parts = input_text_fn.split(os.sep)
#         fn_prefix = fn_parts[-1].split('.')[0]
#         input_json_fn = os.path.join(*fn_parts[:-2],
#                                      'input_json',
#                                      fn_prefix + '.json')
#         output_json_fn = os.path.join(*fn_parts,
#                                       'output_json',
#                                       fn_prefix + '.json')


if __name__ == '__main__':
    if check_hand_created_samples() == True:
        print('Samples are good')
    else:
        print('Some samples are bad')
