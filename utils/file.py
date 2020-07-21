import os
import glob
import json


def read_file(fn):
    with open(fn, 'r') as f:
        return f.read()


def write_file(fn, data):
    with open(fn, 'w') as f:
        f.write(data)


def copy_file(src, dst):
    write_file(dst, read_file(src))


def file_exists(filename):
    return os.path.isfile(filename)


def get_json_from_file(fn):
    with open(fn, 'r') as f:
        return json.load(f)


def write_json_to_file(fn, data):
    with open(fn, 'w') as f:
        s = json.dumps(data, indent=4)
        f.write(s)


def get_filenames(*paths):
    paths = list(paths)
    print(f'paths: {paths}')
    return glob.iglob(os.path.join(paths[0], *paths[1:]))


def ensure_dir_exists(dirname):
    print(f'dirname: {dirname}')
    if not os.path.exists(dirname):
        os.makedirs(dirname)
