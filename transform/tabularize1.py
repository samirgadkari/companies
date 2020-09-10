import traceback
import pandas as pd
from utils.text import remove_all_trailing_As


def clean_string(str):
    return bytes(str, 'utf-8').decode('ascii', 'ignore')


def tabularize1(df):
    '''
    Use the right positional value to group
    the data into the correct columns.
    Since our columns have numbers in them,
    we're going to assume they're right-justified.
    Most of the tables have right-justified numbers,
    but we cannot guarantee it.
    '''
    def create_json(table_number_interpretation, table_years_months, df):

        result = {'table_number_interpretation': table_number_interpretation,
                  'table_years_months': table_years_months}
        table_data = []
        for i in range(len(df)):
            row = df.iloc[i, :]
            name, values = row['text'], row.iloc[1:].values.tolist()
            table_data.append({'name': name,
                               'values': list(map(str, values))})
        result['table_data'] = table_data
        return result

    def transitions(line_nums):
        diffs = line_nums.diff()
        transitions = diffs[diffs < 0].index.values
        return transitions

    def process_header(header):
        header['middle'] = header['left'] + header['width'] / 2
        max_right = header['right'].max()
        min_left = header['left'].min()
        middle_pos = min_left + (max_right - min_left) / 2
        quarter_pos = middle_pos / 2
        header['grouping'] = \
            header['middle'].apply(lambda mid:
                                   'left' if mid < quarter_pos else 'right')
        table_number_interpretation = \
            ' '.join(header[header.grouping == 'left']['text'].values)
        table_years_months = header[header.grouping == 'right']['text'].values
        table_years_months = [text for text in table_years_months
                              if len(text) > 1]

        amounts = header[header.amount.notnull()]
        num_columns = len(amounts)

        num_pieces = len(table_years_months) // num_columns
        result = []
        for i in range(0, num_pieces * num_columns, num_pieces):
            result.append(' '.join(table_years_months[i:i+num_pieces]))
        table_years_months = result

        table_number_interpretation = clean_string(table_number_interpretation)
        table_years_months = [clean_string(x) for x in table_years_months]

        return table_number_interpretation, \
            table_years_months, \
            num_columns

    try:
        transitions = transitions(df.line_num)
        if len(transitions) == 0:
            # No header?
            raise ValueError(f'No header? len(transition) = {len(transitions)}')
        elif len(transitions) > 1:
            # Too many sections?
            raise ValueError(f'Too many sections? len(transition) = '
                            f'{len(transitions)}')

        header = df[df.index < transitions[0]].copy()

        table_number_interpretation, table_years_months, num_columns = \
            process_header(header)

        df2 = df[df.index >= transitions[0]].copy()

        row_headings = df2[df2.amount.isnull()][['line_num', 'text']] \
            .groupby('line_num')['text'] \
            .apply(lambda xs: ' '.join(xs))
        row_headings = remove_all_trailing_As(row_headings)
        row_headings = row_headings.to_frame()

        df2 = df2[['line_num', 'right', 'amount']]
        amounts = df2.groupby('line_num')['amount'].apply(list)
        amounts = amounts.apply(lambda xs: xs[-num_columns:])
        amounts = amounts.to_frame()
        df3 = row_headings.merge(amounts, how='outer',
                                 left_index=True,
                                 right_index=True)

        names = ['amount' + str(col_num) for col_num in range(num_columns)]
        df3[names] = pd.DataFrame(df3.amount.tolist(), index=df3.index)
        df3 = df3.drop('amount', axis=1)
        df3['text'] = df3['text'].apply(clean_string)

        return create_json(table_number_interpretation,
                           table_years_months, df3), ''
    except (ValueError, IndexError, AssertionError, TypeError,
            ZeroDivisionError) as e:
        return None, traceback.format_exc() + '\n\n'
        e = e  # To remove PEP8 error since e isn't used.

