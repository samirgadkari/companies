import subprocess


def find_tables(input_dirname, table_types):
    '''
    Input:
      input_dirname: path of directory within which to find.
      table_types:   list of names of table types to find.
    Output:          list of filenames matching the table types.
    '''
    stdouts = {}
    stderrs = {}
    for table_type in table_types:

        # With capture output set, both standard error and
        # standard out will be captured into pipes.
        completed_process = subprocess.run(['grep', '-r', '-l', table_type, input_dirname],
                                           capture_output=True)

        stdouts[table_type] = completed_process.stdout.decode('utf-8').split('\n')
        stderrs[table_type] = completed_process.stderr.decode('utf-8')
        print(stdouts[table_type])
        # print(stderrs[table_type])

    return stdouts, stderrs
