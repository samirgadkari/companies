import sys
from data.get.get_10Ks_selenium import get_10Ks
from data.get.get_companies_in_sector import get_companies
from data.extract.extract_tables import extract_tables
from data.extract.filter import filter_data
from data.generate.generate import check_hand_created_samples
from data.generate.generate import generate_samples
# from data.transform.html import html
from data.transform.html.table import create_table
from data.transform.html.to_image import html_to_image
from data.extract.text_from_image import image_to_data


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
        'create_table':   create_table,
        'html_to_image':  html_to_image,
        'image_to_data':  image_to_data,
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
