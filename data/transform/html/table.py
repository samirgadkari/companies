import sys
import re
from utils.file import read_file
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
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

        self.df = self.create_dataframe()
        self.cell_data()
        self.value_locations()
        with pd.option_context('display.max_rows', None,
                               'display.max_columns', None):
            print(self.df)

        sys.exit(0)


    def add_rows(self):
        rows = []
        for row_tag in self.table_tag.find_all('tr'):
            rows.append(Row(row_tag))
        return rows


    def value_locations(self):
        df = self.df

        def amount(value):
            matches = Cell.text_amount.search(value.replace(',', ''))
            if matches is None:
                return None
            else:
                try:
                    result = float(''.join(matches.groups()))
                    if value[0] == '(':
                        return -result
                    else:
                        return result
                except ValueError as e:
                    return None # Not all strings are numbers

        df['amount'] = df['text'].apply(lambda text: amount(text))

        years = [str(x) for x in range(1990, 2200)]
        def year(text):
            if text in years:
                return int(text)
            else:
                return None

        df['year'] = df['text'].apply(lambda text: year(text))


    def cell_data(self):
        df = self.df

        def update_alignment(cell):
            matches = Cell.text_align_attr.search(cell['style'])
            if matches is None:
                return Cell.TEXT_ALIGN_LEFT
            else:
                return Cell.alignment_mapping[matches.group(1)]

        df['alignment'] = df['cell'].apply(lambda cell: update_alignment(cell))

        def update_span(cell, type_):
            try:
                return int(cell[type_])
            except KeyError as e:
                return 1

        df['rowspan'] = df['cell'].apply(lambda cell_tag: update_span(cell_tag, 'rowspan'))
        df['colspan'] = df['cell'].apply(lambda cell_tag: update_span(cell_tag, 'colspan'))

        df['text'] = df['cell'].apply(lambda cell_tag:
                                          str(cell_tag.text).strip()) \
                               .str.replace('\xa0', '', flags=re.MULTILINE) \
                               .str.replace('\n', '', flags=re.MULTILINE)


    def create_dataframe(self):
        # import pdb; pdb.set_trace()
        df_input = {'row': [], 'cell': []}
        idx = 0
        for row in self.rows:
            for cell in row.cells:
                df_input['row'].append(row.row_tag)
                df_input['cell'].append(cell.cell_tag)
        return pd.DataFrame(data=df_input)


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


def create_table():
    table = Table('./data/extract/samples/html/html_input/1.html')
    print(table.rows)


if __name__ == '__main__':
    create_table('./data/extract/samples/html/html_input/1.html')
