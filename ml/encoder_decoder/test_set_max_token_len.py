import os
from progress.bar import ChargingBar
from utils.file import read_file, get_filenames
from utils.environ import tables_extracted_split_tables_dir


def test_set_max_token_len():
    print('Getting filenames ...', end=' ')
    base_path = tables_extracted_split_tables_dir()
    fns = list(get_filenames([os.path.join(base_path,
                                           '*',
                                           '10-k',
                                           '*',
                                           '*.table-extracted')]))
    print('done.')
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
    test_set_max_token_len()
