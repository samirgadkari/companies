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

    text_amount = re.compile(r'^\s*[\$]?\(?([\d\.,]*)\)?$')

    def __init__(self, cell_tag):
        self.cell_tag = cell_tag


    def __repr__(self):
        return f'text: {self.cell_tag}'
