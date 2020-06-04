import io
import sys
from PIL import Image
import pytesseract
import numpy as np
import pandas as pd
from utils.text import (amount, remove_single_nonletters)


def col_right_pos(df):
    '''
    Use their right positional value to group
    the data into the correct columns.
    Since our columns have numbers in them,
    we're going to assume they're right-justified.
    '''
    df2 = df.copy()
    df2 = df2[['line_num', 'right', 'amount']]
    df2 = df2[df2['amount'].notnull()]
    df2['amount_tuple'] = df2[['right', 'amount']].apply(tuple, axis=1)
    df2 = df2.drop(columns=['right', 'amount'])

    grouped = df2.groupby('line_num')
    max_num_columns = 0
    for name, group in grouped:
        # print(f'name: {name}\n{group}')
        if len(group) > max_num_columns:
            max_num_columns = len(group)

    groups = []
    for _, group in grouped:
        group2 = group.copy()
        group2['col'] = np.arange(len(group2))
        group = group2.pivot(index='line_num',
                             columns='col', values='amount_tuple')
        groups.append(group)

    tupled = pd.concat(groups, axis=0)
    non_null_tupled = tupled.dropna(axis=0)
    averages = non_null_tupled.apply(lambda col:
                                     col.apply(lambda x: x[0]).mean(),
                                     axis=0)

    def move_values(row):

        if row.isnull().sum() == 0:
            return row

        output_row = pd.Series([None] * len(row))
        for loc in range(len(row)):
            if row[loc] is None:
                continue
            if not isinstance(row[loc], tuple):
                continue

            best_col = -1
            min_dist = np.Inf
            for col in range(len(averages)):
                dist = np.abs(row[loc][0] - averages[col])
                if dist < min_dist:
                    min_dist = dist
                    best_col = col

            output_row[best_col] = row[loc]

        return output_row

    tupled = tupled.apply(move_values,
                          axis=1)
    import pdb; pdb.set_trace()
    sys.exit(0)


def image_to_data(filename):
    # Get verbose data including boxes, confidences, line and page numbers
    data = pytesseract.image_to_data(Image.open(filename))

    # Convert data to dataframe
    df = pd.read_csv(io.BytesIO(str.encode(data)), encoding='utf8',
                     delimiter='\t')

    # Select columns of dataframe, and drop rows that have any nulls.
    df = df[['line_num', 'word_num', 'top', 'left', 'width', 'text']] \
        .dropna(axis=0)

    # Remove specific characters like '$'
    df['text'] = df['text'] \
        .apply(str) \
        .apply(remove_single_nonletters)
    df = df.dropna(axis=0)

    # The right index value is 1 beyond the valid right index
    df['right'] = df['left'] + df['width'] + 1

    df['amount'] = df['text'].apply(amount)

    col_avg_right_pixel_position = col_right_pos(df)

    last_top = None

    def top_pixel_group_func(x):
        nonlocal last_top

        _, top, _, _, _, _, _ = df.loc[x]
        if last_top is None:
            last_top = top
            return top
        elif np.abs(last_top - top) <= 10:
            return last_top
        else:
            last_top = top
            return top

    rows = []
    grouped = df.groupby(by=top_pixel_group_func)
    for name, group in grouped:
        amounts = group[group['amount'].notnull()]
        texts = group[group['amount'].isnull()]
        # print(f'name: {name}\ngroup: {group}\ntexts: {texts}\n'
        #       f'amounts: {amounts}\n')
        if len(amounts) > 0:
            row = pd.DataFrame(data=amounts['amount']).T
            row.index = [' '.join(texts['text'].values)]
            row.columns = ['col' + str(i)
                           for i in range(len(amounts))]
            rows.append(row)
            # print(f'row: {row}\n\n')
        else:
            # print(f'col_headings: {" ".join(texts)}')
            pass

    table = rows[0].append(rows[1:])
    print(table)


if __name__ == '__main__':
    image_to_data('~/out.png')
