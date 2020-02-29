import sys
from get_data.get_10Ks_selenium import get_10Ks
from get_data.get_companies_in_sector import get_companies
from extract_data.extract_tables import extract_tables
from extract_data.filter import filter_data
from generate_data.generate import check_hand_created_samples
from generate_data.generate import generate_samples

if __name__ == '__main__':
    try:
        function_ = sys.argv[1]
    except IndexError:
        raise SystemExit(f'Usage: {sys.argv[0]} '
                         '<"extract_tables|get_10Ks|get_companies>"')
    switcher = {
        'extract_tables': extract_tables,
        'check_hand_created_samples': check_hand_created_samples,
	'generate_samples': generate_samples,
        'get_10Ks':       get_10Ks,
        'get_companies':  get_companies,
        'filter':         filter_data,
    }
    func = switcher.get(function_, lambda: "nothing")
    func()

