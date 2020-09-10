import sys
from get_10Ks import get_10Ks
from data.get.get_companies_in_sector import get_companies
from extract.extract import extract_all_tables
from extract.filter import filter_data
from generate.generate import check_hand_created_samples, generate_samples
from generate.select_tables import select_tables
from transform.tabularize3.table import create_table
from transform.html_to_json import all_html_to_json
from ml.clean_tables import clean_all_tables
from ml.find_all_tag_names import find_unprocessed_tag_names
from ml.encode import find_training_encodings, find_validation_encodings
from ml.encode import encode_training_files, encode_validation_files, \
    encode_test_files
from ml.decode import decode_training_files, decode_validation_test_files
from unescape import unescape_all_tables
from ml.validation_test_split import test_matching_filenames

if __name__ == '__main__':
    try:
        function_ = sys.argv[1]
    except IndexError:
        raise SystemExit(f'Usage: {sys.argv[0]} '
                         '<"extract_tables|get_10Ks|get_companies>"')
    switcher = {
        'check_hand_created_samples': check_hand_created_samples,
        'generate_samples': generate_samples,
        'select_tables': select_tables,
        'get_10Ks':       get_10Ks,
        'get_companies':  get_companies,
        'filter':         filter_data,
        'create_table':   create_table,
        'all_html_to_json':   all_html_to_json,
        'extract_all_tables': extract_all_tables,
        'clean_all_tables': clean_all_tables,
        'find_unprocessed_tag_names': find_unprocessed_tag_names,
        'find_training_encodings': find_training_encodings,
        'find_validation_encodings': find_validation_encodings,
        'encode_training_files': encode_training_files,
        'encode_validation_files': encode_validation_files,
        'encode_test_files': encode_test_files,
        'decode_training_files': decode_training_files,
        'decode_validation_test_files': decode_validation_test_files,
        'unescape_all_tables': unescape_all_tables,
        'test_matching_filenames': test_matching_filenames,
    }
    func = switcher.get(function_, lambda: "nothing")
    if len(sys.argv) > 2:
        if function_ == 'create_table':
            table = func(*sys.argv[2:])
            print(table.to_json())
        else:
            func(*sys.argv[2:])
    else:
        func()
