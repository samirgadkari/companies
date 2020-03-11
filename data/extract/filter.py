import os
import json
import glob
from decouple import config
from datetime import datetime

def all_data():
    data_dir_location = config('DATA_DIR')
    filenames = list(glob.iglob(os.path.join(
        data_dir_location,
        '0*',
        '10-k',
        '*')))

    fns = dict()
    prefix_len = len(data_dir_location) + 1 # +1 removes '/' after prefix
    for fn in filenames:
        dir_name = '/'.join(fn.split('/')[:-2])
        key, value = (fn[prefix_len:].split('/')[0],
                      (dir_name,
                       int(fn[prefix_len:].split('/')[-1][:4])))
        if key in fns:
            fns[key][1].append(value[1])
        else:
            fns[key] = (dir_name, [value[1]])
    return fns


def split_company_dataset(fns):
    current_year = datetime.now().year
    num_incomplete = 0;        incomplete_data = []
    num_young = 0;             young_companies = []
    num_out_of_business = 0;   out_of_business_companies = []
    num_useable = 0;           useable_data = []

    for key, v in fns.items():
        if v[1] is None:
            continue
        value = v[1]
        min_year, max_year = min(value), max(value)
        expected_years = range(min_year, max_year)
        all_years_present = all([year in value
                                 for year in expected_years])

        if all_years_present == False:
            incomplete_data.append(v[0])
            num_incomplete += 1
            fns[key] = (v[0], None)
        elif max_year - min_year < 10:
            if (current_year - max_year) < 2: # Since all companies must file 10-k,
                                              # any who have not are out of business.
                young_companies.append(v[0])
                num_young += 1
                fns[key] = (v[0], None)
            else:
                out_of_business_companies.append(v[0])
                num_out_of_business += 1
                fns[key] = (v[0], None)
        else:
            useable_data.append(v[0])
            num_useable += 1

    result = {'num_incomplete': num_incomplete,
              'incomplete_data': incomplete_data,
              'num_young': num_young,
              'young_companies': young_companies,
              'num_out_of_business': num_out_of_business,
              'out_of_business_companies': out_of_business_companies,
              'num_useable': num_useable,
              'useable_data': useable_data,
              'all_data': fns}
    return result

def remove_marked_companies(fns):
    useable_data = []
    for key, v in fns.items():
        if v[1] is None:
            continue
        useable_data.append(v[0])
    return useable_data


def save_output(fns, data_split):
    filename = os.path.join(config('DATA_DIR'), 'filtered_filenames')
    with open(filename, 'w') as f:
        f.write('\n'.join(fns))

    filename = os.path.join(config('DATA_DIR'), 'all_data')
    with open(filename, 'w') as f:
        json.dump(data_split, f, indent=4)


def filter_data():
    filenames = all_data()
    data_split = split_company_dataset(filenames)
    filenames = remove_marked_companies(data_split['all_data'])
    save_output(filenames, data_split)


if __name__ == '__main__':
    filter_data()
