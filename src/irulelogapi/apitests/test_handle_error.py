import unittest
import flaminglog.logrule as flaminglog

class TestHandleError(unittest.TestCase):


    def test_correct_error_messages(self):

        expErrorDict = {
                0:"",
                1000:("Invalid Input File: Unequal number of entries/exits in"
                    " input log file\n Check: make sure there are equal number"
                    " of entries and exits for each occurrence tpye in the log"
                    " file."),
                1001:("Invalid Input File: Occurrence found at unexpected"
                    " level in input file file\n Check: Make sure the hierarchy"
                    " of occurrences in the input file is the following: EVENT,"
                    " RULE, RULEVM, BYTECODE, CMDVM, CMD. Items can be missing"
                    " in this hierarchy but they must be consistently missing"
                    " throughout the entire file."),
                1002:("Invalid Input File: One or more entries in input file"
                " contain a greater than expected number of data fields"),
                1003:("Invalid Input File: One or more entries in input file"
                    " contain a smaller than expected number of data fields"),
                1004:("Invalid Type Filter or Input File: BYTECODE must not be"
                    " lowest level filtered.\n Check: EVENT, RULE, and/or"
                    " RULEVM must be filtered with BYTECODE. Also check that"
                    " the log file"" contains EVENT, RULE, and/or RULEVM")
        }

        codesToTest = [0, 1000, 1001, 1002, 1003, 1004]

        for code in codesToTest:
            testFailMsg = "Error Code: " +  str(code) + " had wrong message."
            self.assertTrue(
                    flaminglog.handle_error(code) == expErrorDict[code],
                    testFailMsg
            )

    def test_undefined_error(self):
        errorCode = 777
        expMsg = "ERROR: Undefined error code: " + str(errorCode)

        self.assertTrue(
                flaminglog.handle_error(errorCode) == expMsg,
                "Expected error code 777 to be undefined"
        )



if __name__ == '__main__':
    unittest.main()
