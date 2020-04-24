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


def get_json_from_file(fn):
    with open(fn, 'r') as f:
        return json.load(f)


def write_json_to_file(fn, data):
    with open(fn, 'w') as f:
        s = json.dumps(data, indent=4)
        f.write(s)


def get_filenames(*paths):
    return glob.iglob(os.path.join(*paths))
