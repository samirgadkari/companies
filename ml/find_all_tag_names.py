from bs4 import BeautifulSoup
from utils.file import get_filenames, read_file
from utils.environ import extracted_tables_dir
from utils.html import find_descendant_tag_names, tag_actions


def find_unprocessed_tag_names():
    unprocessed_tags = set()
    unprocessed_tags_exist = False
    for filename in get_filenames(extracted_tables_dir(),
                                  '*', '10-k', '*', '*', '*'):
        table_tag = BeautifulSoup(read_file(filename), 'html.parser')

        descendant_tag_names = find_descendant_tag_names(table_tag.descendants)

        diff = descendant_tag_names - set(tag_actions.keys())

        unprocessed_tags.update(diff)
        if len(diff) > 0:
            unprocessed_tags_exist = True
            print(f'filename: {filename}')
            print(f'unprocessed_tags: {unprocessed_tags}')

    if unprocessed_tags_exist:
        print(f'unprocessed_tags: {unprocessed_tags}')
    else:
        print('No unprocessed tags found')


if __name__ == '__main__':
    find_unprocessed_tag_names()
