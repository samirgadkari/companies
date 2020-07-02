from decouple import config


def extracted_tables_dir():
    return config('EXTRACTED_TABLES_DIR')


def data_dir():
    return config('DATA_DIR')
