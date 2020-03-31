import re

class Cell():

    text_align_attr = re.compile(r'text-align\s*:\s*(left|center|right)',
                                 re.MULTILINE | re.IGNORECASE)

    TEXT_ALIGN_LEFT = 0
    TEXT_ALIGN_CENTER = 1
    TEXT_ALIGN_RIGHT= 2
    alignment_mapping = { 'left': TEXT_ALIGN_LEFT,
                          'center': TEXT_ALIGN_CENTER,
                          'right': TEXT_ALIGN_RIGHT }

    def __init__(self, cell_tag):
        self.cell_tag = cell_tag
        self.alignment = Cell.TEXT_ALIGN_LEFT
        self.rowspan = 1
        self.colspan = 1
        self.update_alignment()
        self.update_rowspan()
        self.update_colspan()
        self.text = self.clean(cell_tag.text)


    def update_start_stop_rows(self, cur_row):
        self.start_row = cur_row
        self.stop_row = cur_row + self.rowspan
        return self.stop_row


    def update_start_stop_cols(self, cur_col):
        self.start_col = cur_col
        self.stop_col = cur_col + self.colspan
        return self.stop_col


    def clean(self, text):
        replacements = [('\xa0', ''), ('\n', '')]
        for given_text, replacement_text in replacements:
            text = text.replace(given_text, replacement_text)
        return text


    def update_alignment(self):
        matches = Cell.text_align_attr.search(self.cell_tag['style'])
        if matches is not None:
            self.alignment = Cell.alignment_mapping[matches.group(1)]


    def update_rowspan(self):
        try:
            self.rowspan = int(self.cell_tag['rowspan'])
        except KeyError as e:
            pass # Ignore this exception -
                 # most tds will not have span set


    def update_colspan(self):
        try:
            self.colspan = int(self.cell_tag['colspan'])
        except KeyError as e:
            pass # Ignore this exception -
                 # most tds will not have span set


    def __repr__(self):
        return f'text: {self.text}, ' \
               f'alignment: {self.alignment}, ' \
               f'rowspan: {self.rowspan}, ' \
               f'(start/stop row): {(self.start_row, self.stop_row)}, ' \
               f'colspan: {self.colspan}, ' \
               f'(start/stop col): {(self.start_col, self.stop_col)}'
