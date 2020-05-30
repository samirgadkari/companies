import io
import sys
from PIL import Image
import pytesseract
import numpy as np
import pandas as pd
from utils.text import (amount, remove_single_nonletters)


def col_right_pos(df):
    df2 = df.copy()
    df2 = df2[['line_num', 'right', 'amount']]
    df2  = df2[df2['amount'].notnull()]
    for name, group in df2.groupby('line_num')[['line_num', 'right']]:
        print(f'name: {name}\n{group}')

    # df['reverse_word_num'] = 
    # max_right_pos_per_line = df.groupby('line_num')['right'].max()
    # print(f'max right pos: {max_right_pos_per_line}')
    sys.exit(0)


def image_to_data(filename):
    data = pytesseract.image_to_data(Image.open(filename))
    df = pd.read_csv(io.BytesIO(str.encode(data)), encoding='utf8',
                     delimiter='\t')

    df2 = df[['line_num', 'word_num', 'top', 'left', 'width', 'text']] \
        .copy() \
        .dropna(axis=0)
    df2['text'] = df2['text'] \
        .apply(str) \
        .apply(remove_single_nonletters)
    df3 = df2.copy().dropna(axis=0)
    df3['right'] = df3['left'] + df3['width']

    df4 = df3[df3['text'].apply(lambda x: len(x.strip()) != 0)].copy()
    df4['amount'] = df3['text'].apply(amount)

    last_top = None

    def top_pixel_group_func(x):
        nonlocal last_top

        _, top, _, _, _, _, _ = df4.loc[x]
        if last_top is None:
            last_top = top
            return top
        elif np.abs(last_top - top) <= 10:
            return last_top
        else:
            last_top = top
            return top

    col_avg_right_pixel_position = col_right_pos(df4)

    rows = []
    grouped = df4.groupby(by=top_pixel_group_func)
    for name, group in grouped:
        amounts = group[group['amount'].notnull()]
        texts = group[group['amount'].isnull()]
        print(f'name: {name}\ngroup: {group}\ntexts: {texts}\n'
              f'amounts: {amounts}\n')
        if len(amounts) > 0:
            row = pd.DataFrame(data=amounts['amount']).T
            row.index = [' '.join(texts['text'].values)]
            row.columns = ['col' + str(i)
                           for i in range(len(amounts))]
            rows.append(row)
            print(f'row: {row}\n\n')
        else:
            print(f'col_headings: {" ".join(texts)}')

    table = rows[0].append(rows[1:])
    print(table)


if __name__ == '__main__':
    image_to_data('~/out.png')
