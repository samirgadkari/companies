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
        '''
        For a row with null values in it,
        compare each cell position to the average position values,
        and place the cell in the correct position.
        If this is not done, a row might contain these values:
        Row heading 1       1.2   2.3   NaN   NaN
        instead of:
        Row heading 1       NaN   1.2   NaN   2.3
        '''

        # Ignore rows with no null values in it.
        if row.isnull().sum() == 0:
            return row

        output_row = pd.Series([None] * len(row))
        for loc in range(len(row)):
            if row[loc] is None:
                continue
            if not isinstance(row[loc], tuple):
                continue

            # Compare the position to the average positions of
            # each column to find the best column for this value.
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
    out_df = tupled.applymap(lambda x: x[1] if x is not None else np.nan)
    return out_df


def leftmost_amount_pos(df):
    '''
    Returns the leftmost pixel position of any non-null amount
    in the entire table.
    '''
    df2 = df[['left', 'amount']]
    leftmost_pos = df2[df2.amount.notnull()].left.min()
    return leftmost_pos


def rightmost_text_pos(df):
    '''
    Returns the rightmost text position of any text cell
    in the entire table.
    A text cell is found when the amount is NaN.
    '''
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


def find_dollar_multiplier(cell_texts):

    cell_texts = " ".join([s.lower() for s in cell_texts])
    if "dollar" in cell_texts:
        multiplier_dict = {'thousands': 1_000.0,
                           'millions':  1_000_000.0,
                           'billions':  1_000_000_000.0}
        for key, value in multiplier_dict.items():
            if key in cell_texts:
                dollar_multiplier = value
                return dollar_multiplier

    # Return dollar multiplier of 1.0 if no nultiplier found
    return 1.0


def flag_percentage_row(df):

    non_null_amounts = df[df['amount'].notnull()]

    # If there are no amounts, return the original dataframe
    if len(non_null_amounts) == 0:
        return df

    first_value_idx = non_null_amounts.index[0]

    # If there are only amounts, and no row headings,
    # return original dataframe
    if first_value_idx == 0:
        return df

    # Get the text value of the first amount
    text = df.loc[first_value_idx].text

    # If the end of the text value is %,
    # append the '(percent)' flag at the end
    # of the row heading
    if text[len(text) - 1] == '%':
        # import pdb; pdb.set_trace()

        replacement_text = df.loc[first_value_idx - 1] \
                             .text + '(percent)'
        df.loc[first_value_idx - 1, 'text'] = replacement_text

    return df


def image_to_data(filename):
    def to_json(df):
        '''Converts dataframe table to JSON.
        Split orientation saves the most amount of space
        on disk.
        '''
        return df.to_json(orient='split')

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
        group = grouped.get_group(i).copy()

        group = flag_percentage_row(group)
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
            dollar_multiplier = find_dollar_multiplier(cell_texts)
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
                          str(i),
                          empty_row,
                          allow_duplicates=True)
        df_amounts = df_amounts.T

        # Reset index to remove the names of the columns inserted.
        df_amounts.reset_index()

    df_amounts, col_headings = move_years(df_amounts, col_headings)
    df_amounts = \
        df_amounts.set_index(pd.Series(row_headings))
    df_amounts.columns = col_headings

    # Make sure to replace any None values in the table with np.NaN
    df_amounts.fillna(value=np.nan, inplace=True)

    # Multiply amounts with dollar multiplier so that we can compare
    # different tables that may have different multipliers.
    # applymap() function applies to all cells.
    # After applying, revert back for those cells that are percentages.
    idx = list(df_amounts.index)
    def update_non_percent_amounts(row):
        idx = row.name
        if idx.endswith('(percent)'):
            return row
        else:
            return row * dollar_multiplier

    df_amounts = df_amounts.apply(update_non_percent_amounts, axis=1)
    index = pd.Series(df_amounts.index) \
        .apply(lambda x: x[:-9] if x.endswith('(percent)') else x)
    df_amounts.index = index
    print(df_amounts)
    # print(to_json(df_amounts))


if __name__ == '__main__':
    image_to_data('~/out.png')
