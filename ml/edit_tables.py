import os
import re
from bs4 import BeautifulSoup, Comment
from utils.environ import extracted_tables_dir, \
                          cleaned_tags_dir
from utils.file import get_filenames, write_file, \
                       read_file, ensure_dir_exists
from utils.html import tag_actions


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


def remove_comments(table_tag):
    comments = table_tag.find_all(text=lambda t: isinstance(t, Comment))
    for comment in comments:
        comment.extract()  # Note that decompose does not work for Comments.


def remove_tags(table_tag):

    # We cannot use a recursive approach since the dictionary
    # containing the tags will change as we update them.
    # Instead, go through each type of tag and clean them.
    for tag_name in tag_actions.keys():
        selected_tags = table_tag.find_all(tag_name)
        for tag in selected_tags:
            clean_tag(tag, tag_actions[tag_name])

    # Since we're not using tag name to find the comments,
    # this routine is separated from the code above.
    remove_comments(table_tag)

    # Any changes such as removing tags may cause two
    # NavigableString tags to come next to each other.
    # This will combine those tags, so it becomes
    # renderable HTML.
    table_tag.smooth()

    for tag in table_tag.find_all(True):
        if tag.name not in tag_actions.keys():
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
