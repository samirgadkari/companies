import traceback
import numpy as np
from itertools import repeat

MAX_HEADER_LEN = 7

def tabularize2(df):
    # Usually, &nbsp; (non-breaking space) in HTML converts to
    # A, AA, A$, or AL. Remove these.
    # ae corresponds to a '-' and is required as a placeholder
    # for the cells not having a value.
    # Problem is that A, AA, etc. denote spaces, and may be
    # required for the cells not having a value.
    # So keep all of these and remove those that contain
    # these at the beginning of the row headings.
    # df = df[(df.text != 'A') & (df.text != 'AA') &
    #         (df.text != 'A$') & (df.text != 'AL')]

    def create_json(num_header_rows, table_number_interpretation,
                    table_years_months, lines):

        result = {'table_number_interpretation': table_number_interpretation,
                  'table_years_months': table_years_months}
        table_data = []

        def update(table, name, values):
            values = ["" if isinstance(v, tuple) else v
                      for v in values]
            table.append({'name': name,
                          'values': list(map(str, values))})

        # The sections end when there is an extra space in front
        # of the row header. We dont have that information
        # at this point in the code, so it's commented for now.
        # def get_sections(lines):
        #     sections = []

        #     for i, line in enumerate(lines):
        #         name, values = line['text'], line['data']
        #         # If values are all null, process the section
        #         if len(' '.join(list(map(str, values)))) == 0:
        #             return i + 1, sections
        #         else:
        #             update(sections, name, values)
        #     return i + 1, sections

        i = num_header_rows
        while i < len(lines):
            name, values = lines[i]['text'], lines[i]['data']
            update(table_data, name, values)
            # If values are all null, process the section
            # if len(' '.join(list(map(str, values)))) == 0:
            #     num_lines_processed, sections = get_sections(lines[i + 1:])
            #     import pdb; pdb.set_trace()
            #     table_data.append({'name': name, 'sections': sections})

            #     # Update i for number of lines processed in the section
            #     i += num_lines_processed
            # else:
            #     update(table_data, name, values)
            i += 1  # Update i for the current line processed

        result['table_data'] = table_data
        return result

    def group(lines):
        MIN_PHRASE_HORIZ_SPACING = 50

        grouped_text_lines = []
        for line in lines:
            groups = []
            group = [line['text'][0][2]]
            for i in range(1, len(line['text'])):

                word_tuple = line['text'][i]
                earlier_right, left, text = word_tuple

                if abs(left - earlier_right) < MIN_PHRASE_HORIZ_SPACING:
                    group.append(text)
                else:
                    groups.append(' '.join(group))
                    group = [text]
            groups.append(' '.join(group))

            grouped_text_lines.append({'text': groups,
                                       'data': line['data']})

        return grouped_text_lines

    def get_lines(df):
        COMBINE_TOP_VALUES_WITHIN_DELTA = 10
        group_text = []
        group_data = []
        lines = []
        last_top_value = df.iloc[0].top
        for i in range(1, len(df)):

            cur_top_value = df.iloc[i].top
            text = df.iloc[i].text
            amount = df.iloc[i].amount
            earlier_right = df.iloc[i-1].right
            left = df.iloc[i].left
            if abs(cur_top_value - last_top_value) < \
               COMBINE_TOP_VALUES_WITHIN_DELTA:
                # import pdb; pdb.set_trace()
                if np.isnan(df.iloc[i].amount):
                    if (text == 'A' or text == 'AA' or
                        text == 'A$' or text == 'AL' or len(text) == 0):
                        # These are just the spaces between HTML elements.
                        # Ignore them.
                        continue
                    if text == 'ae':
                        group_data.append((earlier_right, left, np.nan))
                    else:
                        group_text.append((earlier_right, left, text))
                else:
                    group_data.append(df.iloc[i].amount)
            else:
                # import pdb; pdb.set_trace()
                if len(group_text) > 0 or len(group_data) > 0:
                    lines.append({'text': group_text,
                                  'data': group_data})
                    group_text = []
                    group_data = []
                if np.isnan(amount):
                    if (text == 'A' or text == 'AA' or
                        text == 'A$' or text == 'AL' or len(text) == 0):
                        # These are just the spaces between HTML elements.
                        # Ignore them.
                        continue
                    if text == 'ae':
                        group_data.append((earlier_right, left, np.nan))
                    else:
                        group_text.append((earlier_right, left, text))

            last_top_value = cur_top_value

        return group(lines)

    def combine_column_headers(lines, year_value_index, year_month_indexes):

        global MAX_HEADER_LEN

        levels = []
        years = list(map(str, map(int, lines[year_value_index]['data'])))

        indexes = set(year_month_indexes)
        if year_value_index:
            indexes.add(year_value_index)
        num_header_rows = len(indexes)
        if num_header_rows == 0:
            raise ValueError('No header found')

        if len(indexes) == 1:
            index = next(iter(indexes))
            num_header_rows = index + 1
            max_columns = 1
            if index == year_value_index:
                return num_header_rows, max_columns, years
            else:
                return num_header_rows, max_columns, lines[index]['text']

        max_columns = 0
        for index in range(MAX_HEADER_LEN):
            if index == year_value_index:
                levels.append(years)
                max_columns = max(max_columns, len(years))
            elif index in year_month_indexes:
                months = lines[index]['text']
                levels.append(months)
                max_columns = max(max_columns, len(years))

        combined = [x for x in levels]
        for index in range(1, len(levels)):
            len_index = len(levels[index])
            len_earlier_index = len(levels[index - 1])
            if len_index == len_earlier_index:
                combined = \
                    list(map(lambda x: ' '.join(x),
                             zip(levels[index - 1], levels[index])))
                continue

            if len_earlier_index > len_index:
                assert len_earlier_index % len_index == 0, \
                    'Cannot combine col headers\n' \
                    '\tlarger length not a multiple of smaller length.'
                multiple = len_earlier_index // len_index
                combined = \
                    list(map(lambda x: ' '.join(x),
                             zip(levels[index - 1],
                             [x for item in levels[index]
                              for x in repeat(item, multiple)])))
            else:
                assert len_index % len_earlier_index == 0, \
                    'Cannot combine col headers\n' \
                    '\tlarger length not a multiple of smaller length.'
                multiple = len_index // len_earlier_index
                combined = \
                    list(map(lambda x: ' '.join(x),
                             zip([x for item in levels[index - 1]
                                  for x in repeat(item, multiple)],
                                 levels[index])))

        return num_header_rows, max_columns, combined

    def header_info(lines):
        from datetime import datetime
        from calendar import month_abbr

        year_value_string_range = range(1990, datetime.now().year + 1)

        # Find the indexes containing the month strings or 'year'
        year_month_strings = [month_abbr[i].lower() for i in range(1, 13)]
        year_month_strings.extend(['year', 'month'])
        year_month_indexes = []
        for line_idx in range(MAX_HEADER_LEN):
            line = lines[line_idx]
            joined_line_text = ' '.join(line['text']).lower()
            for string in year_month_strings:
                if string in joined_line_text:
                    year_month_indexes.append(line_idx)
                    break

        # Find the index which contains year values
        year_value_index = None
        year_value_strings = [str(i) for i in year_value_string_range]
        for line_idx in range(MAX_HEADER_LEN):
            line = lines[line_idx]
            for string in year_value_strings:
                for x in line['data']:
                    if string in str(x):
                        year_value_index = line_idx
                        break

        # Find the multiplier for each value in the table
        multiplier_strings = ['thousand', 'million', 'billion']
        multiplier = 1

        def find_multiplier(joined_line_text):
            for mult_idx, string in enumerate(multiplier_strings):
                if string in joined_line_text:
                    return 1000**(mult_idx + 1)

        for line_idx in range(MAX_HEADER_LEN):
            joined_line_text = ' '.join(lines[line_idx]['text']).lower()
            multiplier = find_multiplier(joined_line_text) or 1
            if multiplier > 1:
                break

        # Ensure that you found what you were looking for
        if len(year_month_indexes) == 0 or \
           year_value_index is None:
            raise ValueError(f'Could not find where header ends.'
                             f'len(year_month_indexes): '
                             f'{len(year_month_indexes)}'
                             f'year_value_index: {year_value_index}')

        # Process year/month into one string per column.
        num_header_rows, num_columns, column_headers = \
            combine_column_headers(lines, year_value_index, year_month_indexes)

        indexes = set(year_month_indexes)
        if year_value_index:
            indexes.add(year_value_index)

        table_number_interpretation = \
            ' '.join([lines[i]['text'] for i in range(num_header_rows)
                      if i not in indexes])

        return num_header_rows, column_headers, multiplier, \
            table_number_interpretation

    try:
        lines = get_lines(df)
        num_header_rows, table_years_months, multiplier, \
            table_number_interpretation = header_info(lines)

        for line in lines:
            if isinstance(line['text'], list):
                line['text'] = ' '.join(line['text'])

        return create_json(num_header_rows, table_number_interpretation,
                           table_years_months, lines), ''
    except (ValueError, IndexError, AssertionError, TypeError,
            ZeroDivisionError) as e:
        return None, traceback.format_exc() + '\n\n'
        e = e  # To remove PEP8 error since e isn't used.

