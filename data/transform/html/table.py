import re
from utils.file import read_file
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import json
from .cell import Cell  # text_align_attr
from .row import Row


class Table():

    MIN_COL = 0
    MAX_COL = 300  # We don't expect more than 300 columns in a table

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
        self.table = self.build_table()
        # with pd.option_context('display.max_rows', None,
        #                        'display.max_columns', None):
        #     print(self.df)
        #     print(f'values_start_row: {self.values_start_row} '
        #           f'values_end_row:   {self.values_end_row}')
        #     print(f'values_start_col: {self.values_start_col} '
        #           f'values_end_col: {self.values_end_col}')

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
                    if '(' in value:
                        return -result
                    else:
                        return result
                except ValueError:
                    return None  # Not all strings are numbers

        df['amount'] = df['text'].apply(lambda text: amount(text))

        def row_headings(text):
            if len(text) == 1 and text[0] in '$%)()—':
                return None

            num_digits_in_text = len(list(filter(str.isdigit, text)))
            num_chars_in_text = len(text)
            if num_chars_in_text > 0 and \
               (num_chars_in_text -
                    num_digits_in_text)/num_chars_in_text > 0.5:
                return text
            else:
                return None

        df['row_headings'] = df['text'].apply(lambda text: row_headings(text))
        years = [str(x) for x in range(1990, 2200)]

        def year(text):
            if text in years:
                return int(text)
            else:
                return None

        df['year'] = df['text'].apply(lambda text: year(text))

        def col_nums():

            df_idx = 0
            df_colspans = df['colspan']
            df_alignments = df['alignment']
            df['col_start'] = None
            df['col_end'] = None
            row_idx = 0
            df['row_start'] = None
            df['row_end'] = None
            for num_cols in self.num_cols_per_row:
                col_count = 0
                num_values_in_col = 0

                while num_values_in_col < num_cols:
                    df.loc[df_idx, 'row_start'] = row_idx
                    df.loc[df_idx, 'row_end'] = row_idx + 1

                    if df_colspans[df_idx] == 1:
                        df.loc[df_idx, 'col_start'] = col_count
                        df.loc[df_idx, 'col_end'] = col_count + 1
                        col_count += 1
                    elif df_colspans[df_idx] > 1:
                        if df_alignments[df_idx] == Cell.TEXT_ALIGN_LEFT:
                            df.loc[df_idx, 'col_start'] = col_count
                            df.loc[df_idx, 'col_end'] = col_count + 1
                        elif df_alignments[df_idx] == Cell.TEXT_ALIGN_CENTER:
                            location = col_count + df_colspans[df_idx] // 2
                            df.loc[df_idx, 'col_start'] = location
                            df.loc[df_idx, 'col_end'] = location + 1
                        else:
                            location = col_count + df_colspans[df_idx]
                            df.loc[df_idx, 'col_start'] = location
                            df.loc[df_idx, 'col_end'] = location + 1
                        col_count += df_colspans[df_idx]
                    else:
                        raise ValueError('Invalid colspan value')
                    num_values_in_col += 1
                    df_idx += 1

                row_idx += 1

        col_nums()

        self.values_start_col = \
            df.iloc[np.where(df['amount'].notnull())]['col_start'].min()
        self.values_end_col = \
            df.iloc[np.where(df['amount'].notnull())]['col_end'].max()
        self.values_start_row = \
            df.iloc[np.where(df['amount'].notnull())]['row_start'].min()
        self.values_end_row = \
            df.iloc[np.where(df['amount'].notnull())]['row_end'].max()

    def build_table(self):

        start_row_amounts = (self.df[self.df['year'].notnull()]
                                    ['row_start']).max()
        selected = self.df[['row_start', 'row_headings',
                            'col_start', 'amount']].copy()
        selected = selected[selected.row_start > start_row_amounts]

        # Not sure why this is happening. It looks like we're using
        # df.loc[] as required to not get this warning, but we're
        # still getting it. Remove it for now.
        mode_chained_assignment = pd.get_option('mode.chained_assignment')
        pd.set_option('mode.chained_assignment', None)

        # Pivot so that we have:
        # - row headings as row names
        # - start columns as column names
        # - amounts as values
        # in the table.
        pivoted = []
        for name, group in selected.groupby('row_start'):
            # The row heading is at a different index,
            # compared to the row values.
            single_row_heading = \
                ' '.join(group[group.row_headings.notnull()].row_headings)
            group.loc[:, 'row_headings'] = single_row_heading

            # Pivot the non-null amounts.
            # We keel all the pivoted dataframes, so we can
            # combine them together later. This will be
            # more efficient.
            nonzero_amounts = group[group.amount.notnull()].copy()
            pivoted.append(nonzero_amounts.pivot_table(index='row_headings',
                                                       columns='col_start',
                                                       values='amount'))

        # Reset the SettingWithCopyWarning message
        pd.set_option('mode.chained_assignment', mode_chained_assignment)

        # Combine pivoted dataframes together
        combined = pivoted[0].append(pivoted[1:])

        # If adjacent column names are 1 value off, combine them.
        # Let's see if this heuristic works for all tables.
        def group_columns(cols, diff=1):
            col_groups = []
            last_col = cols[0]
            group = (last_col, last_col)
            for col in cols[1:]:
                if last_col + diff >= col:
                    group = (last_col, col)
                else:
                    col_groups.append(group)
                    last_col = col
                    group = (last_col, last_col)
            col_groups.append(group)

            return col_groups

        col_groups = group_columns(combined.columns.astype('int').values,
                                   diff=1)

        def merge_columns(df, col_groups):
            def merge_func(x, y):
                if x is None or np.isnan(x):
                    return y
                if y is None or np.isnan(y):
                    return x
                raise ValueError('Both columns contain values - '
                                 'cannot merge!!', x, y)

            merged = []
            for start, end in col_groups:
                start_col = np.argwhere(df.columns.values == start)[0][0]
                end_col = np.argwhere(df.columns.values == end)[0][0]
                col_values = df.iloc[:, start_col]
                for col in range(start_col+1, end_col+1):
                    col_values = \
                        col_values.combine(df.iloc[:, col], merge_func)
                merged.append(col_values)

            merged = pd.concat(merged, axis=1)
            return merged

        merged = merge_columns(combined, col_groups)

        def find_dollar_multiplier(row_headings):
            bools = row_headings.dropna(axis=0)['row_headings'] \
                                .str.contains('Dollar', case=False)

            dollar_mult_map = {'hundred': 100,
                               'thousand': 1_000.,
                               'million': 1_000_000,
                               'billion': 1_000_000_000}

            dollar_multiplier_str = row_headings[bools]['row_headings'] \
                .values[0].lower()
            for key in dollar_mult_map.keys():
                if key in dollar_multiplier_str:
                    return bools, dollar_mult_map[key]
            else:
                raise ValueError('Dollar multiplier not found !!')

        def col_headings(start_row_amounts, num_cols, df):
            selected = self.df[['row_start', 'row_headings',
                                'col_start', 'amount', 'year']].copy()
            selected = selected[selected.row_start <=
                                start_row_amounts]

            row_headings = selected[['row_start', 'row_headings']].copy()
            row_headings = row_headings.dropna(axis=0)
            dollar_str_bools, dollar_mult = \
                find_dollar_multiplier(row_headings)
            row_headings = row_headings[~dollar_str_bools]
            num_row_headings = len(row_headings)

            year = selected[['row_start', 'year']].copy()
            year = year.dropna(axis=0)
            num_years = len(year)

            if (num_cols % num_row_headings != 0) or \
               (num_cols % num_years != 0) or \
               ((num_row_headings > num_years) and
                (num_row_headings % num_years != 0)) or \
               ((num_row_headings < num_years) and
                    (num_years % num_row_headings != 0)):
                raise ValueError('Invalid number of columns vs col headings')

            def merge_col_headings(rh, years):
                col_headings = []
                for idx in range(len(years)):
                    col_headings.append(rh[idx] + '\n' + str(int(years[idx])))
                return col_headings

            if num_row_headings < num_years:
                years = year.year.values
                mult = num_years // num_row_headings
                rh = row_headings.row_headings \
                                 .apply(lambda x: [x]*mult).tolist()
                rh = [z for x in rh for z in x]
                return merge_col_headings(rh, years)
            elif num_row_headings > num_years:
                rh = row_headings.row_headings.values
                mult = num_row_headings // num_years
                years = years.apply(lambda x: [x]*mult).tolist()
                years = [z for x in years for z in x]
                return merge_col_headings(rh, years)
            else:
                return merge_col_headings(row_headings.row_headings.values,
                                          years)
            raise ValueError('Should not come here - ever !!')

        column_headings = \
            col_headings(start_row_amounts,
                         merged.shape[1],
                         self.df)
        merged.columns = column_headings
        print(merged)
        return merged

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
            except KeyError:
                return 1

        df['rowspan'] = df['cell'].apply(lambda cell_tag:
                                         update_span(cell_tag, 'rowspan'))
        df['colspan'] = df['cell'].apply(lambda cell_tag:
                                         update_span(cell_tag, 'colspan'))

        df['text'] = df['cell'].apply(lambda cell_tag:
                                      str(cell_tag.text).strip()) \
                               .str.replace('\xa0', '', flags=re.MULTILINE) \
                               .str.replace('\n', '', flags=re.MULTILINE)

    def create_dataframe(self):
        df_input = {'row': [], 'cell': []}
        self.num_cols_per_row = []
        for row in self.rows:
            self.num_cols_per_row.append(len(row.cells))
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
                tag.unwrap()  # remove the surrounding tag from content

    def to_json(self):
        '''Converts dataframe table to JSON'''
        # 'split' orientation saves the most amount of space
        # on disk.
        return self.table.to_json(orient='split')


def create_table(filename):
    return Table(filename)


if __name__ == '__main__':
    table = create_table('./data/extract/samples/html/html_input/1.html')
    print(f'table.table: {table.table}')
    print(f'JSON: {table.to_json()}')
