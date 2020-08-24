from ml.number import NumberSequence
from ml.tokens import is_number_token


def convert_dict_values(number_dict):
    return {k: str(v) for k, v in number_dict.items()}


def update_seq_and_number_dict(values, token_seq, word_num,
                               number_dict, reverse_number_dict):

    for value in values:
        # If NumberSequence, it is a number in NavigableString.
        if isinstance(value, NumberSequence):
            num_seq = value
            if num_seq in reverse_number_dict:
                token_seq.append(reverse_number_dict[num_seq])
            else:
                key = f'num_{word_num}'
                number_dict[key] = num_seq
                reverse_number_dict[num_seq] = key
                word_num += 1
                token_seq.append(key)
        else:
            token_seq.append(value.strip())

    return word_num


def encode_token(token, tokens, number_dict,
                 encoded_num_start_value_shift):
    if is_number_token(token) and token in number_dict:
        num = number_dict[token]

        # shift the number sequence start value to
        # maximum value of the tokens + 1
        result = list(NumberSequence(num.start +
                                     encoded_num_start_value_shift,
                                     num.negative,
                                     num.number,
                                     num.fraction, num.percent,
                                     num.end))
        if result is None:
            raise ValueError('Result is None')
        return result
    else:
        result = tokens[token]
        if result is None:
            raise ValueError('Result is None')
        return result


def encode_file(filename, token_seq, tokens, number_dict,
                encoded_num_start_value_shift):

    encoded_str = []
    encoded_values = [encode_token(token, tokens, number_dict,
                                   encoded_num_start_value_shift)
                      for token in token_seq]
    for values in encoded_values:
        if isinstance(values, list):
            for value in values:
                encoded_str.append(str(value))
        else:
            encoded_str.append(values)
    encoded = ' '.join(encoded_str)

    with open(filename + '.encoded', 'w') as f:
        f.write(encoded)
