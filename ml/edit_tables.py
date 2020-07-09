import os
import re
from bs4 import BeautifulSoup
from utils.environ import extracted_tables_dir, \
                          cleaned_tags_dir
from utils.file import get_filenames, write_file, \
                       read_file, ensure_dir_exists


attrs_regex = re.compile(r'\w+\[(.*?[,\\])]')


def remove_tag_attrs(tag, keep_attrs):
    for attr in list(tag.attrs.keys()):
        if attr not in keep_attrs:
            del tag[attr]


def clean_tag(tag, directions):
    if 'untouched' in directions:
        return
    elif 'remove_attrs_except' in directions:
        parts = directions[len('remove_attrs_except')+1:]
        parts = directions[:-1].split(',')
        parts = [part[1:] if part[0] == ' ' else part for part in parts]
        remove_tag_attrs(tag, parts)
    elif 'unwrap' in directions:
        tag.unwrap()
    elif 'decompose' in directions:
        tag.decompose()


def remove_tags(table_tag):

    # tag.unwrap(): removes the tag and it's attributes,
    # but keeps the text inside.
    # tag.decompose(): completely removes a tag and it's contents.
    # tag.clear(): removes just the contents (insides) of the tag,
    # not the tag itself.
    clean_tags = {
        'html':          'untouched',
        'body':          'untouched',
        'table':         'untouched',
        'tr':            'remove_attrs_except[rowspan, colspan, style]',
        'td':            'remove_attrs_except[rowspan, colspan, style]',
        'div':           'unwrap',
        'font':          'unwrap',
        'p':             'unwrap',
        'br':            'decompose',
    }

    # We cannot use a recursive approach since the dictionary
    # containing the tags will change as we update them.
    # Instead, go through each type of tag and clean them.
    for tag_name in clean_tags.keys():
        selected_tags = table_tag.find_all(tag_name)
        for tag in selected_tags:
            clean_tag(tag, clean_tags[tag_name])

    # Any changes such as removing tags may cause two
    # NavigableString tags to come next to each other.
    # This will combine those tags, so it becomes
    # renderable HTML.
    table_tag.smooth()

    for tag in table_tag.find_all(True):
        if tag.name not in clean_tags.keys():
            tag.decompose()

    table_tag.smooth()


def edit_all_tables():
    for filename in get_filenames(extracted_tables_dir(),
                                  '*', '10-k', '*', '*', '*'):
        print(f'filename: {filename}')
        table_tag = BeautifulSoup(read_file(filename), 'html.parser')

        remove_tags(table_tag)

        filename_suffix = filename[len(extracted_tables_dir()):]
        out_filename = cleaned_tags_dir() + filename_suffix
        out_dirname_parts = out_filename.split(os.sep)[:-1]
        ensure_dir_exists(os.path.join(os.sep, *out_dirname_parts))

        write_file(out_filename, table_tag.prettify())


if __name__ == '__main__':
    edit_all_tables()
