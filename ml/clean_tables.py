import os
from bs4 import BeautifulSoup, Comment
from utils.environ import extracted_tables_dir, generated_html_json_dir, \
                          cleaned_tags_dir
from utils.file import get_filenames, write_file, \
                       read_file, ensure_dir_exists, \
                       file_exists

# tag.unwrap(): removes the tag and it's attributes,
# but keeps the text inside.
# tag.decompose(): completely removes a tag and it's contents.
# tag.clear(): removes just the contents (insides) of the tag,
# not the tag itself.
# This table shows the tag name and action to take on the tag.
tag_actions = {
    'a':              'unwrap',
    'b':              'untouched',
    'big':            'unwrap',
    'br':             'decompose',
    'body':           'untouched',
    'c':              'decompose',
    'caption':        'decompose',
    'center':         'untouched',
    'dd':             'decompose',
    'dl':             'decompose',
    'dir':            'decompose',
    'div':            'unwrap',
    'dt':             'decompose',
    'em':             'untouched',
    'f1':             'decompose',
    'f2':             'decompose',
    'f3':             'decompose',
    'f4':             'decompose',
    'f5':             'decompose',
    'f6':             'decompose',
    'f7':             'decompose',
    'f8':             'decompose',
    'f9':             'decompose',
    'f10':            'decompose',
    'f11':            'decompose',
    'f1':             'decompose',
    'fn':             'decompose',
    'font':           'unwrap',
    'h1':             'remove_attrs_except[style]',
    'h2':             'remove_attrs_except[style]',
    'h3':             'remove_attrs_except[style]',
    'h4':             'remove_attrs_except[style]',
    'h5':             'remove_attrs_except[style]',
    'h6':             'remove_attrs_except[style]',
    'hr':             'untouched',
    'html':           'untouched',
    'i':              'unwrap',
    'ix:nonfraction': 'unwarp',
    'ix:nonnumeric':  'unwrap',
    'img':            'decompose',
    'li':             'decompose',
    'nobr':           'unwrap',
    None:             'untouched',  # The None name is for the HTML Comment tag
    'p':              'unwrap',
    'page':           'decompose',
    's':              'decompose',
    'small':          'unwrap',
    'span':           'decompose',
    'sup':            'decompose',
    'sub':            'decompose',
    'strong':         'untouched',
    't':              'decompose',
    'table':          'untouched',
    'td':             'remove_attrs_except[rowspan, colspan, style]',
    'th':             'remove_attrs_except[rowspan, colspan, style]',
    'tr':             'remove_attrs_except[rowspan, colspan, style]',
    'u':              'untouched',
    'ul':             'decompose',
}


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


def clean_all_tables():
    for filename in get_filenames(extracted_tables_dir(),
                                  '*', '10-k', '*', '*', '*'):
        filename_suffix = filename[len(extracted_tables_dir()):]
        out_filename = cleaned_tags_dir() + filename_suffix
        if file_exists(out_filename):
            continue

        print(f'filename: {filename}')
        table_tag = BeautifulSoup(read_file(filename), 'html.parser')

        remove_tags(table_tag)

        out_dirname_parts = out_filename.split(os.sep)[:-1]
        ensure_dir_exists(os.path.join(os.sep, *out_dirname_parts))

        write_file(out_filename, table_tag.prettify())


if __name__ == '__main__':
    clean_all_tables()
