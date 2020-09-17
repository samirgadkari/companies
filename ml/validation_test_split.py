'''
We need a consistent way of creating testing/validation sets.
Training sets will be generated from samples in separate code,
and will be split with weights of [100, 0] which ensures all
files in the directory will be part of the training set.

Algorithm:
0. If the file containing the validation/testing information
   exists, load it. If not, continue to step 1.
1. Get the list of filenames matching the search pattern.
   Since glob is not consistent in the order of filenames returned,
   sort the filenames.
2. Create a list the same size as the filenames list,
   but with 0/1 values.
   0 => file is selected for validation
   1 => file is selected for testing
   Weights will be provided to specify the number of files used
   for validation, and those for testing.
   Training sets will be generated from files in this directory,
   but only a few will be used to generate huge sets.
   The training files will not be removed when creating the
   validation/test sets.
3. Save the filename and selector lists in a single dictionary.
4. When asked, return the list of validation/testing files
5. Save the dictionary in a JSON file inside the directory
   where the files were obtained.
'''
import os
import random
import numpy as np
from utils.file import get_filenames, get_json_from_file, \
    write_json_to_file
from utils.environ import cleaned_tags_dir

FILETYPE_TRAINING = 0
FILETYPE_VALIDATION = 1
FILETYPE_TESTING = 2
VALIDATION_FILE_PERCENT = 80.0
TEST_FILE_PERCENT = 20.0


# Initialize the random number generator to ensure
# we will get the same results each time it's
# functions are called. This gives you repeatability,
# which helps when debugging.
def init_rng():
    random.seed(32)


# cum_weights = cumulative weights for the validation and testing sets.
# If the cum_weights are [80, 20], then 80% of the filenames
# will be used for validation, and 20% for testing.
def validation_test_selectors(num_filenames,
                              weights=[VALIDATION_FILE_PERCENT,
                                       TEST_FILE_PERCENT]):
    return random.choices([FILETYPE_VALIDATION,
                           FILETYPE_TESTING], weights=weights, k=num_filenames)


def training_selectors(num_filenames):
    return random.choices([FILETYPE_TRAINING], weights=[100], k=num_filenames)


def select_filenames(filenames, selectors, filename_type):
    names = np.array(filenames)
    select_names = np.array(selectors)
    return names[select_names == filename_type]


def selectors_contain_filename_type(selectors, filename_type):
    return any(x == filename_type for x in selectors)


def matching_filenames(saved_filenames_path,
                       all_filename_paths,
                       filename_type=0,
                       selector_weights=[VALIDATION_FILE_PERCENT,
                                         TEST_FILE_PERCENT]):
    '''
    selector_weights: For training, selector weights will be [100, 0].
    This is so we can use all the files for training. Our training
    files are not the original ones - each will be generated.
    For validation/testing, we want selector weights to be [80, 20].
    This means we will validate on 80% of our actual files,
    and test on 20%.
    '''

    init_rng()  # Initialize the random number generator.

    try:
        names = get_json_from_file(saved_filenames_path)

        # This will allow us to regenerate the filenames list
        # for the new filename type that is passed in.
        if not selectors_contain_filename_type(names['selectors'],
                                               filename_type):
            raise FileNotFoundError

        return select_filenames(names['filenames'],
                                names['selectors'],
                                filename_type)
    except FileNotFoundError:
        all_filenames = []
        for paths in all_filename_paths:
            all_filenames.extend(get_filenames(paths))

        # Some of our directories will have files which have been processed.
        # Ignore those files by filtering them out.
        all_filenames = [fn for fn in all_filenames if
                         fn.endswith(('html', 'json',
                                      'expected_json',
                                      'table-extracted',
                                      'unescaped'))]
        all_filenames.sort()

        if filename_type == FILETYPE_TRAINING:
            selectors = training_selectors(len(all_filenames))
        else:
            selectors = validation_test_selectors(len(all_filenames),
                                                  selector_weights)
        names = {'filename_type': filename_type,
                 'filenames': all_filenames,
                 'selectors': selectors}
        write_json_to_file(saved_filenames_path, names)
        return select_filenames(names['filenames'],
                                names['selectors'],
                                filename_type)


def test_matching_filenames(training):
    paths = [os.path.join(cleaned_tags_dir(),
                          '*', '10-k', '*', '*', '*.unescaped')]
    saved_filenames_path = os.path.join(cleaned_tags_dir(),
                                        'validation_test_split')
    if int(training) == FILETYPE_TRAINING:
        print('Training test')
        training_filenames = matching_filenames(saved_filenames_path,
                                                paths,
                                                FILETYPE_TRAINING)
        print(f'len(training_filenames): {len(training_filenames)}')
    else:
        print('Validation/testing test')
        validation_filenames = matching_filenames(saved_filenames_path,
                                                  paths,
                                                  FILETYPE_VALIDATION)
        test_filenames = matching_filenames(saved_filenames_path,
                                            paths,
                                            FILETYPE_TESTING)

        if len(set(validation_filenames) & set(test_filenames)) != 0:
            print(f'Error !! Some filenames in validation also in test.')

        print(f'len(validation_filenames): {len(validation_filenames)}')
        print(f'len(test_filenames): {len(test_filenames)}')

        num_validation_files = len(validation_filenames)
        num_test_files = len(test_filenames)
        total_num_files = num_validation_files + num_test_files

        validation_file_percent = num_validation_files/total_num_files * 100.
        test_file_percent = num_test_files/total_num_files * 100.
        if abs(validation_file_percent - VALIDATION_FILE_PERCENT) < 0.1 and \
           abs(test_file_percent - TEST_FILE_PERCENT) < 0.1:
            print(f'Correct validation/test ratio of files selected')
        else:
            print(f'Error !! Incorrect validation/test ratio '
                  f'of files selected')
        print('validation_file_percent: {:4.1f}'
              .format(validation_file_percent))
        print('test_file_percent: {:4.1f}'.format(test_file_percent))
