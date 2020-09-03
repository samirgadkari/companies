import os
import traceback
from utils.environ import generated_html_json_dir, html_samples_dir
from utils.file import get_filenames, write_json_to_file
from .html_to_image import html_to_image
from .image_to_json import image_to_json


def html_to_json():
    output_dirname = os.path.join(generated_html_json_dir(),
                                  'samples',
                                  'generated_json')
    os.makedirs(output_dirname, exist_ok=True)

    for full_filepath in get_filenames(html_samples_dir(), 'html_input', '*'):
        full_filepath = './data/extract/samples/html/html_input/1.html'
        filename = full_filepath.split(os.sep)[-1].lower()

        if not filename.endswith('html'):
            continue
        print(f'full_filepath: {full_filepath}')

        try:
            html_to_image(full_filepath)
            json_data = image_to_json('out.png')

            output_filename = os.path.join(output_dirname,
                                           filename.split('.')[0] + '.json')
            print(f'output_filename: {output_filename}')
            write_json_to_file(output_filename, json_data)
        except Exception as e:
            print(traceback.format_exc())
            e = e  # To remove PEP8 error since e isn't used.
        break


def all_html_to_json():
    html_to_json()
