import io
from PIL import Image
import pytesseract
import numpy as np
import pandas as pd
from utils.text import (amount, remove_single_nonletters)


def tabularize_amounts(df):
    '''
    Use their right positional value to group
    the data into the correct columns.
    Since our columns have numbers in them,
    we're going to assume they're right-justified.
    Most of the tables have right-justified numbers,
    but we cannot guarantee it.
    '''
    df2 = df.copy()
    df2 = df2[['line_num', 'right', 'amount']]
    df2 = df2[df2['amount'].notnull()]
    df2['amount_tuple'] = df2[['right', 'amount']].apply(tuple, axis=1)
    df2 = df2.drop(columns=['right', 'amount'])

    grouped = df2.groupby('line_num')
    max_num_columns = 0
    for name, group in grouped:
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
    out_df = tupled.applymap(lambda x: x[1] if x is not None else None)
    return out_df


def leftmost_amount_pos(df):
    df2 = df[['left', 'amount']]
    leftmost_pos = df2[df2.amount.notnull()].left.min()
    return leftmost_pos


def rightmost_text_pos(df):
    df2 = df[['right', 'amount']]
    rightmost_pos = df2[df2.amount.isnull()].right.max()
    return rightmost_pos


def move_years(df, col_headings):
    try:
        years = df.iloc[0].apply(lambda x: int(x))
    except ValueError as e:
        print(e)
        print('Could not convert first row to years')
        return df, col_headings

    years_range = range(1990, 2200)
    data_are_years = \
        len(df.iloc[0]) == \
        years.apply(lambda x: x in years_range).sum()

    if not data_are_years:
        return df, col_headings

    multiplier = len(years) // len(col_headings)
    headings = []
    for i in range(0, len(years)):
        headings.append(
            col_headings[i // multiplier] + ' ' + str(years[i]))

    return df.iloc[1:], headings


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

    df_amounts = tabularize_amounts(df)

    left_amount_pos = leftmost_amount_pos(df)

    col_headings = []
    row_headings = []
    grouped = df.groupby('line_num')
    insert_empty_row_at = []

    # We range over the length of the group keys since the sequence
    # of the keys in a dictionary could be different,
    # and we want our table rows in order.
    for i in range(1, len(grouped.groups.keys()) + 1):
        group = grouped.get_group(i)
        right_text_pos = rightmost_text_pos(group)
        texts = group[group.amount.isnull()]
        if right_text_pos > left_amount_pos:
            cell_texts = [texts.iloc[0].text]
            for i in range(len(texts) - 1):
                if np.abs(texts.iloc[i].right -
                          texts.iloc[i+1].left) < 10:
                    cell_texts.append(texts.iloc[i+1].text)
                else:
                    if not ((len(cell_texts) == 1) and
                            (len(cell_texts[0]) == 0)):
                        col_headings.append(" ".join(cell_texts))
                    cell_texts = [texts.iloc[i+1].text]
        else:
            row_headings.append(" ".join(texts.text))
        amounts = group[group.amount.notnull()]
        if len(amounts) == 0:
            insert_empty_row_at.append(i - 1)

    empty_row = [None] * df_amounts.shape[1]
    for i in insert_empty_row_at:

        # Since we cannot insert rows, but we can insert columns,
        # transpose the dataframe, insert the row as a column,
        # and then transpose the dataframe back.
        df_amounts = df_amounts.T
        df_amounts.insert(i,
                          str(i) + " added",
                          empty_row,
                          allow_duplicates=True)
        df_amounts = df_amounts.T

        # Reset index to remove the names of the columns inserted.
        df_amounts.reset_index()

    df_amounts, col_headings = move_years(df_amounts, col_headings)
    df_amounts = \
        df_amounts.set_index(pd.Series(row_headings))
    df_amounts.columns = col_headings
    print(df_amounts)


if __name__ == '__main__':
    image_to_data('~/out.png')
