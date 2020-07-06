import sys
import os
from . import testsuites
from . import testframe
if __name__ == '__main__':

    verbosity = 2
    verbosity = os.environ.get(
            'TEST_VERBOSITY',
            verbosity
    )

    runnumber = 1
    runnumber = os.environ.get(
            'TEST_RUN_NUMBER',
            runnumber
    )

    inputfile = 'apitests/TestLogs/mainlog2.txt'
    inputfile = os.environ.get(
            'TEST_INPUT_FILE',
            inputfile
    )

    testsuites.run_full_suite(int(verbosity))
    testframe.remove_all_temp_files()
    

