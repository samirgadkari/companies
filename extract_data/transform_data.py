
# Notes on how to process text tables.
#
# 0. Sometimes, a single line at the top of the table
# will have <S> for where the subject column begins,
# and <C> for where each value column begins.
# Ignore this line, as these tags are approximate locations.
# Instead find the column edges by looking
# at where the values start for each column. Then split the columns.
# This is probably a good thing to do before doing anything else.
# 0.5 Sometimes, column headings are multi-line.
# If so, combine them to get the actual column heading.
# 1. If there are notes at the end of the string, remove them.
# They're in the form (Note 1) or (Notes 1 and 7).
# 2. If there is no number at the end of the line,
# and the next line does not have preceding spaces,
# then that line names the upcoming block.
# 3. If there is no number at the end of the line,
# and the next line starts with more spaces,
# then the previous line names the upcoming block.
# 4. If there are only lines with '---' or '===' and spaces,
# ignore them
# 5. There may be 'in thousands', 'in millions', 'in billions'.
# Note this number down in the block it is specifying.
# 6. If the numbers at the end of the line represent years,
# note their positions, and values. Their positions tell us
# where the text columns are approximately. Their values
# will be used to tag the dollar values of each cell.
# 7. Value columns may contain '$' (in dollars),
# ',' (within the number), '-' (value unknown), '()' (negative values).
# Process them accordingly.
#
import re
from functools import reduce


top_of_table = re.compile(r'^(.*?)(\s{2,})(\d{4}\s*)+$', re.MULTILINE)
first_col_len = re.compile(r'^(.*?)\s{2,}', re.MULTILINE)
other_col_len = re.compile(r'^(.*?)(\$?\s{2,}\$?([,.\s\d]+)?)$', re.MULTILINE)


def column_header_location(data):
    pass


def top_of_table(data):
    m = top_of_table.match(data)
    if m:
        start = m.start(0)
        end = m.end(0)
        return (start, end)

    raise(ValueError, 'Could not find the top of the table')


def bottom_of_table(data):
    return len(data)


def col_sizes(data):
    m = first_col_len.match(data)
    col_lengths = []
    if m:
        col_lengths.append(reduce(max, map(len, m.groups)))
    else:
        raise(ValueError, 'Could not find first column length')

    # Remove first column data so it will be easier to process
    # remaining columns.
    row_num = 0
    def remove_first_col_data(row):
        other_columns = row[col_lengths[row_num]]
        row_num += 1
        return other_columns
    other_columns = map(remove_first_col_data, data.split('\n'))
    other_columns = map(strip, other_columns)  # Remove leading and trailing spaces


def years_shown(data):
    pass


def segment_table(data):
    pass


def clean_segments(segments):
    pass


def build_output(segments):
    pass


def find_grid_locations(data):
    top_of_table = top_of_table(data)
    bottom_of_table = bottom_of_table(data)
    name_width, data_widths = col_sizes(data[top_of_table:bottom_of_table])

    segments = segment_table(data)
    cleaned = clean_segments(segments)

    return build_output(cleaned)
