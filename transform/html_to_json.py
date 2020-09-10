import os
import traceback
from utils.environ import generated_html_json_dir, html_samples_dir
from utils.file import get_filenames, write_json_to_file, copy_file, \
    write_file
from .html_to_image import html_to_image
from .image_to_json import image_to_json


def html_to_json():
    output_dirname = os.path.join(generated_html_json_dir())
    os.makedirs(output_dirname, exist_ok=True)

    result_string = ''
    num_all_files = 0
    num_files_processed = 0
    for full_filepath in get_filenames(html_samples_dir(), 'html_input', '*'):
        # full_filepath = './data/extract/samples/html/html_input/1.html'
        filename = full_filepath.split(os.sep)[-1].lower()

        if not filename.endswith('table-extracted'):
            continue
        print(f'{num_all_files}: full_filepath: {full_filepath}')
        result_string += full_filepath + '\n'

        num_all_files += 1
        html_to_image(full_filepath)
        json_data, error_str = image_to_json('out.png')
        if json_data is None:
            result_string += traceback.format_exc() + '\n\n'
        else:
            num_files_processed += 1
            output_filename = \
                os.path.join(output_dirname,
                            filename.split('.')[0] + '.json')
            print(f'output_filename: {output_filename}')
            write_json_to_file(output_filename, json_data)

            output_html_filename = os.path.join(output_dirname,
                                                filename)
            copy_file(full_filepath, output_html_filename)

    result_stats = f'num_files_processed: {num_files_processed}\n' \
        f'num_all_files: {num_all_files}\n' \
        f'success ratio: {num_files_processed / num_all_files}\n'
    print(result_stats)
    result_string += result_stats
    write_file(os.path.join(output_dirname, 'html_to_json_processing_results'),
               result_string)


def all_html_to_json():
    html_to_json()
