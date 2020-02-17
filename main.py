import sys
from get_data.get_10Ks_selenium import get_10Ks
from get_data.get_companies_in_sector import get_companies
from extract_data.extract_tables import extract_tables

if __name__ == '__main__':
    try:
        function_ = sys.argv[1]
    except IndexError:
        raise SystemExit(f'Usage: {sys.argv[0]} '
                         '<"extract_tables|get_10Ks|get_companies>"')
    switcher = {
        'extract_tables': extract_tables,
        'get_10Ks':       get_10Ks,
        'get_companies':  get_companies
    }
    func = switcher.get(function_, lambda: "nothing")
    func()

