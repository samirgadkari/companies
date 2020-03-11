from utils.html_utils import Soup
from utils.file_utils import *

generated_samples_dir = config('GENERATED_SAMPLES_DIR')


def encode_file(filename):
    return soup.prettify()

def encode_html(filename):
    data = shorten_file(filename)  TODO
    all_data_keys = set()
    pos = 0
    for item, item_len in next_tag_or_data(data[pos:]):
        all_data.add(item)
        pos += item_len
    all_data = {}
    value = 0; all_data['<sos>'] = value
    value = 1; all_data['<unk>'] = value
    value = 2; all_data['<pad>'] = value
    value = 3; all_data['<eos>'] = value
    value = 4
    for key in all_data_keys:
        all_data[key] = value
        value += 1


def encode():
    html_files = get_filenames(generated_samples_dir, '*.html')
    encodings = map(encode_html, html_files)
    return encodings

if __name__ == '__main__':
    encode()
