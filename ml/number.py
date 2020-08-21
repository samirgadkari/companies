import re
from enum import Enum
from math import modf
from dataclasses import dataclass

FRACTION_MULT_DIV = 100.0
regex_any_digits = re.compile(r'\d', re.MULTILINE)
regex_number = re.compile(r'^\$?\s*(\(?[\d\,]*?\.?[\d]*\)?)\%?$', re.MULTILINE)


# These are the hard-coded numbers that are output for particular conditions.
class Number(Enum):
    PADDING = 0
    START_SEQUENCE = 10
    END_SEQUENCE = 11

    # This will be the starting key ('num_' + this value as a string)
    # for the number file. It will also be the starting key
    # (this value as a string) for the tokens file.
    START_WORD_NUM = 100


@dataclass(init=True, repr=False, eq=False, order=False,
           unsafe_hash=False, frozen=False)
class NumberSequence:
    start: int
    negative: int
    number: int
    fraction: int
    percent: int
    end: int

    def __repr__(self):
        return '(' + str(self.start) + ',' \
            + str(self.negative) + ',' \
            + str(self.number) + ',' \
            + str(self.fraction) + ',' \
            + str(self.percent) + ',' \
            + str(self.end) + ')'

    def __iter__(self):
        self.iter_values = [self.start, self.negative, self.number,
                            self.fraction, self.percent, self.end]
        self.iter_cur = 0
        return self

    def __next__(self):
        if self.iter_cur >= len(self.iter_values):
            raise StopIteration
        result = self.iter_values[self.iter_cur]
        self.iter_cur += 1
        return result

    def __eq__(self, o):
        if isinstance(o, self.__class__):
            return hash(o) == hash(self)
        return NotImplemented

    def __hash__(self):
        # We know that tuples are hashable, so we store
        # our data in a tuple and hash it.
        return hash((self.start, self.negative, self.number,
                     self.fraction, self.percent, self.end))


def convert_fraction_to_whole(num: str) -> str:
    # Check that if the number is a fraction,
    # we can multiply it by 100 and save just
    # the integer part without losing any data.
    # This is because fractions in accounting
    # data are probably percentages.
    # If not, raise an exception.
    num = abs(float(num))
    frac, whole = modf(float(num) * FRACTION_MULT_DIV)

    # Since we're dealing with fractions, the math will not be perfect.
    #    ex: number = 2.55, frac = 0.9999999 whole = 254.0
    # In this case we have to add frac to whole.
    # Then when we truncate using int(), we will get the right value.
    whole = frac + whole
    return str(int(whole))


def convert_whole_to_fraction(num: int) -> float:
    return float(num / FRACTION_MULT_DIV)


def number_to_sequence(is_negative, num_str, is_percent):
    # Many documents contain the % sign in a separate
    # cell from the actual value. We consider the presence
    # of the '.' in the text to denote percentage.
    if '.' in num_str:
        num_str = convert_fraction_to_whole(num_str)

        return NumberSequence(
            Number.START_SEQUENCE.value,
            1 if is_negative else 0,
            int(num_str),
            1,  # this is a fractional number
            1 if is_percent else 0,
            Number.END_SEQUENCE.value)
    else:
        return NumberSequence(
            Number.START_SEQUENCE.value,
            1 if is_negative else 0,
            int(abs(int(num_str))),
            0,  # this is not a fractional number
            1 if is_percent else 0,
            Number.END_SEQUENCE.value)


def is_number(text):
    return bool(regex_number.fullmatch(text))


def digits_in_string(text):
    return bool(regex_any_digits.search(text))


def get_number(text):
    if not digits_in_string(text):
        return (False, False, False)

    match = regex_number.fullmatch(text)

    # If the whole match is not just a period, $, or comma,
    # then we have a valid number.
    if match is not None \
       and match.group(0) not in ['.', '$', ',', '(', ')']:
        is_negative = is_percentage = False

        result = match.group(1)

        # Many documents contain the % sign in a separate
        # cell from the actual value. We consider the presence
        # of the '.' in the text to denote percentage.
        if '.' in text:
            is_percentage = True
        result = result.replace(',', '') \
            .replace('$', '') \
            .replace('%', '')
        if '(' in result or ')' in result:
            result = result.replace('(', '-') \
                .replace(')', '')
            is_negative = True
        if len(result) == 0:
            return (False, False, False)
        return (is_negative, result, is_percentage)
    else:
        return (False, False, False)
