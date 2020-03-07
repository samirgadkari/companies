import re
import json
from bs4 import BeautifulSoup
from utils.file_utils import read_file

class Html():

    text_align_attr = re.compile(r'text-align\s*:\s*(left|center|right)',
                                 re.MULTILINE | re.IGNORECASE)
    TEXT_ALIGN_LEFT = 0
    TEXT_ALIGN_CENTER = 1
    TEXT_ALIGN_RIGHT = 2
    alignment_mapping = { 'left': TEXT_ALIGN_LEFT,
                          'center': TEXT_ALIGN_CENTER,
                          'right': TEXT_ALIGN_RIGHT }

    def __init__(self, filename):
        self.filename = filename
        self.data = read_file(self.filename)
        self.soup = BeautifulSoup(self.data, 'html.parser')
        self.shorten_data()

    def shorten_data(self):
        self.copy_style_attr_to_td()
        self.keep_only_table_related_tags()
        self.keep_only_relevant_attrs()
        self.data = str(self.soup)

    def tags(self):
        return self.soup.find_all(True)

    def text(self):
        return self.soup.get_text()

    def keep_only_relevant_attrs(self):
        tags = self.tags()
        for tag in tags:
            attrs = [attr for attr in tag.attrs.keys()]
            for attr in attrs:
                if attr not in ['rowspan', 'colspan', 'style']:
                    del tag[attr]

    def keep_only_table_related_tags(self):
        table_related_tag_names = set(['table', 'th', 'tr', 'td'])
        all_tag_names = set(map(lambda t: t.name, self.tags()))
        remove_tag_names = all_tag_names.difference(table_related_tag_names)
        for tag_name in remove_tag_names:
            tags = self.soup.find_all(tag_name)
            for tag in tags:
                tag.unwrap() # keep the content, but remove the surrounding tag

    def copy_style_attr_to_td(self):
        tds = self.soup('td')
        for td in tds:
            alignment = 'left'  # By default, text in tds are left-aligned
            elements = td.find_all(style=True)
            for e in elements:
                styles = e['style']
                matches = Html.text_align_attr.search(styles)
                if matches is not None:
                    alignment = matches.group(1)
            td['style'] = f'text-align:{alignment}'

    def to_rows(self):

        def get_span(element, type):
            span = 1
            try:
                span = int(element[type])
            except KeyError as e:
                pass # Ignore this exception -
                     # most tds will not have span set.
            return span

        def get_alignment(element, type):
            alignment = Html.TEXT_ALIGN_LEFT
            matches = Html.text_align_attr.search(element[type])
            if matches is not None:
                alignment = Html.alignment_mapping[matches.group(1)]
            return alignment

        def clean(text):
            replacements = [('\xa0', ''), ('\n', '')]
            for given_text, replacement_text in replacements:
                text = text.replace(given_text, replacement_text)
            return text

        tables = self.soup('table')
        if len(tables) > 1:
            print(f'{soup.filename}: More than one table found')
            return None

        rows = []
        for tr_idx, tr in enumerate(tables[0].find_all('tr')):
            cells = []
            cur_col = 0
            for td_idx, td in enumerate(tr.find_all(['td', 'th'])):
                colspan = get_span(td, 'colspan')
                rowspan = get_span(td, 'rowspan')
                alignment = get_alignment(td, 'style')
                start_col = cur_col
                stop_col = start_col + 1
                start_row = tr_idx
                stop_row = start_row + 1
                if rowspan > 1:
                    stop_row = start_row + rowspan
                if colspan > 1:
                    stop_col = stop_col + colspan
                    cur_col = stop_col
                else:
                    cur_col += 1
                cells.append((start_row, stop_row,
                              start_col, stop_col,
                              alignment,
                              clean(td.text)))
            rows.append(cells)

        return sorted(rows)

    def overlap(self,
                start_1, end_1,
                start_2, end_2):
        set1 = set(list(range(start_1, end_1)))
        set2 = set(list(range(start_2, end_2)))
        if set1.intersection(set2) != set():
            return True
        return False

    def extract_data(self, rows):
        def is_amount(value):
            num_digits_in_value = len(list(filter(str.isdigit, value)))
            num_chars_in_value = len(value)
            if num_chars_in_value > 0 and \
               (num_chars_in_value - num_digits_in_value)/num_chars_in_value < 0.5:
                return True
            else:
                return False

        years = [str(x) for x in range(1990, 2200)]
        def is_year(value):
            if value in years:
                return True
            return False

        def get_all_col_headings(rows,
                                 min_row_with_values,
                                 min_col_with_values):

            def should_merge_col_headings(headings):
                heading_rows = set()
                for h in headings:
                    row_start_h, _, _, _, _, _ = h
                    heading_rows.add(row_start_h)
                if len(heading_rows) > 1:
                    return True
                return False

            def merge_col_headings(headings):
                result = []
                for idx, h1 in enumerate(headings):
                    row_start_h1, row_end_h1, \
                        col_start_h1, col_end_h1, _, value_h1 = h1
                    for h2 in headings[idx+1:]:
                        row_start_h2, row_end_h2, \
                            col_start_h2, col_end_h2, _, value_h2 = h2
                        if row_start_h1 == row_start_h2:
                            continue
                        if self.overlap(col_start_h1, col_end_h1,
                                        col_start_h2, col_end_h2):

                            col_start = min(col_start_h1, col_start_h2)
                            col_end = max(col_end_h1, col_end_h2)
                            combined_text = value_h1 + ' ' + value_h2
                            result_text = [x[2] for x in result]

                            if row_start_h1 < row_start_h2:
                                if combined_text not in result_text:
                                    result.append((col_start,
                                                   col_end,
                                                   combined_text))

                return result

            col_headings = []
            for row in rows:
                for item in row:
                    row_start, row_end, col_start, col_end, _, value = item
                    if row_end <= min_row_with_values and \
                       col_start >= min_col_with_values and \
                       value != '':
                        col_headings.append(item)

            col_headings.sort()
            for heading in col_headings:
                print(f'heading: {heading}')
            if should_merge_col_headings(col_headings):
                col_headings = merge_col_headings(col_headings)
            return col_headings

        def get_all_row_headings(rows, min_col_with_values):
            res = []
            for row in rows:
                for item in row:
                    row_start, row_end, col_start, col_end, _, value = item
                    if col_end <= min_col_with_values + 1 and \
                       value != '':
                        res.append(item)
            return res

        # The values are to the right and bottom of the table.
        # The headers are on the top and on the left of the table.
        # Find the location of the values by checking each cell
        # for digits.
        min_row_with_values = len(rows)
        max_row_with_values = 0
        min_col_with_values = 100  # TODO replace number with actual calculation,
                                   # in case there are some tables with more columns.
        max_col_with_values = 0
        values = []
        for row in rows:
            for item in row:
                row_start, row_end, col_start, col_end, alignment, value = item
                if is_amount(value) and not is_year(value):
                    values.append(item)
                    print(f'item: {item}')
                    if min_row_with_values > row_start:
                        min_row_with_values = row_start
                    if max_row_with_values < row_end:
                        max_row_with_values = row_end
                    if min_col_with_values > col_start:
                        min_col_with_values = col_start
                    if max_col_with_values < col_end:
                        max_col_with_values = col_end

        col_headings = get_all_col_headings(rows,
                                            min_row_with_values,
                                            min_col_with_values)
        row_headings = get_all_row_headings(rows, min_col_with_values)

        print(f'col_headings; {col_headings}')
        print(f'row_headings; {row_headings}')
        return row_headings, col_headings, values

    def data_to_json(self, rows, cols, values):

        def get_row(rows, r_start, r_end):
            for idx, row in enumerate(rows):
                row_start, row_end, _, _, _, row_heading = row
                if r_start >= row_start and r_end <= row_end:
                    return rows[idx][-1]

        def get_col(cols, c_start, c_end, cell_alignment):
            overlaps = []
            for idx, col in enumerate(cols):
                col_start, col_end, col_heading = col
                if self.overlap(c_start, c_end, col_start, col_end):
                    overlaps.append(idx)
            if cell_alignment == Html.TEXT_ALIGN_LEFT:
                return cols[overlaps[0]][-1]
            elif cell_alignment == Html.TEXT_ALIGN_RIGHT:
                return cols[overlaps[-1]][-1]
            else:
                if len(overlaps) > 3:
                    raise ValueError('Should not have more than '
                                     '3 overlapping col regions')
                return cols[overlaps[1]][-1]

        def build_entry(r, c, v):
            return {'row': r, 'col': c, 'value': v}

        entries = []
        for value in values:
            r_start, r_end, c_start, c_end, alignment, v = value
            row = get_row(rows, r_start, r_end)
            col = get_col(cols, c_start, c_end, alignment)
            entry = build_entry(row, col, v)
            entries.append(entry)
        return entries

def test_html():
    html_ = Html('./extract_data/samples/html/html_input/1.html')
    rows = html_.to_rows()
    row_headings, col_headings, values = html_.extract_data(rows)
    json_ = html_.data_to_json(row_headings, col_headings, values)

    with open('1.json', 'w') as f:
        json.dump(json_, f)

if __name__ == '__main__':
    test_html()
