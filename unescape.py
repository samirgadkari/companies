import html
from utils.file import read_file, write_file, get_filenames
from utils.environ import html_samples_dir


def unescape_all_tables():
    for filename in get_filenames(html_samples_dir(),
                                  'html_input', '*'):
        print(f'Un-escaping file: {filename}')
        out_filename = filename[:-1] + '.new'
        converted = html.unescape(read_file(filename))
        write_file(out_filename, converted)


if __name__ == '__main__':
    unescape_all_tables()
