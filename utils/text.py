import re


years = [str(x) for x in range(1990, 2200)]
NUMBER_RE = re.compile(r'^\-?[0-9]*\.?[0-9]*$')


def number(text):
    return NUMBER_RE.search(text) is not None


def remove_single_nonletters(text):
    text = text.strip()
    if (len(text) == 1) and \
       (text[0] == '$'):
        return ''
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
