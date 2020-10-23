import os
from progress.bar import ChargingBar
from utils.file import read_file, get_filenames
from utils.environ import generated_data_dir


def train_set_max_token_len():
    print('Getting filenames ...', end=' ')
    base_path = os.path.join(generated_data_dir())
    fns = list(get_filenames([os.path.join(base_path, 'html', '*.unescaped')]))
    fns.extend(list(get_filenames([os.path.join(base_path, 'expected_json',
                                                '*.expected_json')])))
    print('done')

    bar = ChargingBar('Processing files', max=len(fns))
    max_token_len = 0
    for fn in fns:
        token_len = len(read_file(fn).split())
        if token_len > max_token_len:
            max_token_len = token_len
        bar.next()

    bar.finish()

    with open(os.path.join(base_path, 'max_token_len'), 'w') as f:
        f.write(f'max_token_len: {max_token_len}')


if __name__ == '__main__':
    train_set_max_token_len()
