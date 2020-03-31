from utils.file import read_file
from bs4 import BeautifulSoup
from .cell import Cell  # text_align_attr
from .row import Row


class Table():

    def __init__(self, filename):
        self.filename = filename
        self.data = read_file(self.filename)

        self.table_tag = BeautifulSoup(self.data, 'html.parser')

        # copy attribute from tag that specifies alignment
        # to the td tag. This is needed since we will
        # remove all tags other than table, tr, td, and th.
        self.add_style_attr_to_td()

        self.shorten()
        self.rows = self.add_rows()


    def add_rows(self):
        rows = []
        for row_tag in self.table_tag.find_all('tr'):
            rows.append(Row(row_tag))
        return rows

    def shorten(self):
        self.tags()
        self.attrs()


    def all_tags(self):
        return self.table_tag.find_all(True)


    def add_style_attr_to_td(self):
        tds = self.table_tag('td')
        for td in tds:
            alignment = 'left'  # By default, text in tds are left-aligned
            elements = td.find_all(style=True)
            for e in elements:
                styles = e['style']
                matches = Cell.text_align_attr.search(styles)
                if matches is not None:
                    alignment = matches.group(1)
            td['style'] = f'text-align:{alignment}'


    def attrs(self):
        tags = self.all_tags()
        for tag in tags:
            attributes = [attr for attr in tag.attrs.keys()]
            for attr in attributes:
                if attr not in ['rowspan', 'colspan', 'style']:
                    del tag[attr]


    def tags(self):
        table_tag_names = set(['table', 'th', 'tr', 'td'])
        all_tag_names = set(map(lambda t: t.name, self.all_tags()))
        remove_tag_names = all_tag_names - table_tag_names
        for tag_name in remove_tag_names:
            tags = self.table_tag.find_all(tag_name)
            for tag in tags:
                tag.unwrap() # keep the content, but remove the surrounding tag


def create_table_():
    table = Table('./data/extract/samples/html/html_input/1.html')
    print(table.rows)


def create_table():
    create_table_()


if __name__ == '__main__':
    create_table('./data/extract/samples/html/html_input/1.html')
