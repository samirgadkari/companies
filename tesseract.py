import os
import sys
import traceback
from utils.environ import extracted_tables_dir
from data.transform.html.to_image import html_to_image
from data.extract.text_from_image import image_to_data
from data.extract.find_tables import find_tables
# from glob import iglob


def process_file(fn, table_type, overwrite_files):
    print(f'Filename: {fn}', end=' ')

    table_extracted_filename_suffix = 'table-extracted'
    out_fn = fn[:-len(table_extracted_filename_suffix)] + 'json'
    # If converted file exists, continue processing other files
    if os.path.isfile(out_fn) and not overwrite_files:
        return

    # Converts HTML to PNG. Saves converted data to file out.png
    html_to_image(fn)

    # Converts out.png to JSON
    try:
        json_data = image_to_data('out.png', table_type)

        with open(out_fn, 'w') as f:
            f.write(json_data)
    except Exception as e:
        # We did this to see the filename printed as the last line
        # before the OS returned us to the command prompt.
        # This allowed us not to require scrolling to the top
        # to find the filename.
        print(traceback.format_exc())
        print(f'Filename: {fn}')
        sys.exit(0)


def text_to_json(input_dirname,
                 table_type='Consolidated Balance Sheet',
                 overwrite_files=False):
    '''
    Input: Directory path holding files containing a single HTML table each.
    Output: Directory path holding JSON files for each HTML table file.
    '''
    if input_dirname.endswith('.table-extracted'):
        process_file(input_dirname, table_type, overwrite_files)
    else:
        grep_output, grep_errors = find_tables(input_dirname,
                                               [table_type])

        print('Errors during grep:')
        for table_type, errors in grep_errors.items():
            print(f'  {table_type}:')
            print(f'  {errors}:')

        for table_type, filenames in grep_output.items():
            for fn in filenames:
                process_file(fn, table_type, overwrite_files)


if __name__ == 'main':
    text_to_json(extracted_tables_dir())
