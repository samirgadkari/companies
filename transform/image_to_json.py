import io
from PIL import Image
import pytesseract
import pandas as pd
from utils.text import (amount, remove_single_nonletters)
from .tabularize1 import tabularize1
from .tabularize2 import tabularize2
from .tabularize3.table import tabularize3

MAX_HEADER_LEN = 7
MAX_TOP_DIFF_THRESHOLD = 5
MAX_LEFT_DIFF_THRESHOLD = 100


def image_to_json(filename):

    # Get verbose data including boxes, confidences, line and page numbers
    data = pytesseract.image_to_data(Image.open(filename))

    # Convert data to dataframe
    df = pd.read_csv(io.BytesIO(str.encode(data)), encoding='utf8',
                     delimiter='\t')

    df['bottom'] = df.top + df.height

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

    df_json, error_str = tabularize3(filename)
    if df_json is not None:
        return df_json, error_str

    df_json, error_str = tabularize2(df)
    if df_json is not None:
        return df_json, error_str

    df_json, error_str = tabularize1(df)
    if df_json is not None:
        return df_json, error_str

    return None, ''


if __name__ == '__main__':
    image_to_json('~/out.png')
