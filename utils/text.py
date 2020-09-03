import re
import string


years = [str(x) for x in range(1990, 2200)]
number_re = re.compile(r'^\-?[0-9]*\.?[0-9]*$')
regex_trailing_As = re.compile(r'(?:\s*A\s*)*$')

regex_punctuation = ''
for c in string.punctuation:
    regex_punctuation += f'\\{c}'
split_using_punctuation_re = re.compile(r'\w+|' + f'{regex_punctuation}')


def split_using_punctuation(s):
    return list(map(str.strip,
                    split_using_punctuation_re.findall(s)))


def number(text):
    if len(text) == 1 and text[0] == '-':
        return False

    return number_re.search(text) is not None


def remove_bad_endings(text):
    s = text
    bad_endings = ['\n', '%']
    while len(s) > 0 and s[-1] in bad_endings:
        s = s[:-1]
    # if len(s) < len(text):
    #     print(f'       {text} => {s}')
    return s


def filter_bad_tokens(text):
    if text is None or len(text) == 0 or len(text.strip()) == 0:
        return False
    return True


def remove_single_nonletters(text):
    text = text.strip()
    if (len(text) == 1) and \
       (text[0] == '$'):
        return None
    else:
        return text


def amount(text):
    negative = False

    # If a column heading contains a comma,
    # ex. "Dec 31,", then this is a problem
    # since each word is considered separately.
    # Remove commas only when they appear
    # within the word and not after it.
    # This way ex. 33,256,192 is valid.
    if text[-1:] == ',':
        return None

    if '(' in text:
        negative = True
    text = text.strip() \
               .replace('(', '') \
               .replace(',', '') \
               .replace(')', '') \
               .replace('%', '')
    if len(text) == 0:
        return None

    if not number(text):
        return None

    value = float(text)
    if negative:
        return -value
    else:
        return value


def row_headings(text):
    if len(text) == 1 and text[0] in '$%)()—':
        return None

    num_digits_in_text = len(list(filter(str.isdigit, text)))
    num_chars_in_text = len(text)
    if num_chars_in_text > 0 and \
       (num_chars_in_text -
            num_digits_in_text)/num_chars_in_text > 0.5:
        return text
    else:
        return None


def year(text):
    if text in years:
        return int(text)
    else:
        return None


def remove_all_trailing_As(row_headings):
    return row_headings.transform(lambda x: regex_trailing_As.sub('', x))


def remove_nonascii_chars(str):
    MAX_ASCII_VALUE = 127

    def replace_nonascii(c):
        if ord(c) > MAX_ASCII_VALUE:
            return ' '
        else:
            return c

    result = ''.join(map(replace_nonascii, list(str)))
    return result
