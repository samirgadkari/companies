import os
import glob
import json
import itertools


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


def get_filenames(paths):
    if len(paths) > 1:
        generators = [glob.iglob(path) for path in paths]
        return itertools.chain.from_iterable(generators)
    else:
        return glob.iglob(paths[0])


def ensure_dir_exists(dirname):
    print(f'dirname: {dirname}')
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def remove_files(*paths):
    paths = list(paths)
    for filename in glob.iglob(os.path.join(paths[0], *paths[1:]),
                               recursive=True):
        os.remove(filename)


def create_dirs(dirnames):
    for dirname in dirnames:
      if not os.path.exists(dirname):
          os.makedirs(dirname)
