from decouple import config


def html_samples_dir():
    return config('HTML_SAMPLES_DIR')


def generated_samples_dir():
    return config('GENERATED_SAMPLES_DIR')


def encoded_tables_dir():
    return config('ENCODED_TABLES_DIR')


def extracted_tables_dir():
    return config('EXTRACTED_TABLES_DIR')


def cleaned_tags_dir():
    return config('CLEANED_TAGS_DIR')


def data_dir():
    return config('DATA_DIR')


def tokens_file():
    return config('TOKENS_FILE')
