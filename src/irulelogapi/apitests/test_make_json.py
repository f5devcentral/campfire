import sys, os
import unittest
import json
from . import testframe
import flaminglog.logrule as flaminglog

class TestMakeJson(unittest.TestCase):

    INPUTFILE = os.environ.get('TEST_INPUT_FILE', 'apitests/TestLogs/rawlog.txt')
    RUNNUMBER = int(os.environ.get('TEST_RUN_NUMBER', 1))
    VERBOSITY = int(os.environ.get('TEST_VERBOSITY', 2))

    def do_sub_tests(
            self,
            results,
            exp,
            countCheck,
            levelCheck,
            dataCheck,
            lenCheck
        ):
        """
        Does the actual tests
        """
        countMsg = "FAILED: Count Incorrect\n"
        countMsg += "\tExpected: " + str(exp.count) + "\n"
        countMsg += "\tActual: " + str(results.count) + "\n"
        with self.subTest('Test Count'):
            self.assertTrue(countCheck, countMsg)
        
        dataMsg = "FAILED: Data Inconsistent\n"
        dataMsg += "\tFailed Levels: " + str(results.dataFails)
        with self.subTest('Test Data'):
            self.assertTrue(dataCheck, dataMsg)

        levelMsg = "FAILED: Occurrence found outside expected level\n"
        levelMsg += "\tFailed Levels: " + str(results.levelFails)
        with self.subTest('Test Occurrence Levels'):
            self.assertTrue(levelCheck, levelMsg)

        lenMsg = "FAILED: Actual and Expected have different amounts of data\n"
        with self.subTest('Test Data Length'):
            self.assertTrue(lenCheck, lenMsg)


    def do_error_subtests(
            self,
            outName,
            outList,
            errorCode,
            expName,
            expList,
            expError):

        with self.subTest("outName check"):
            self.assertEqual(outName, expName)
        with self.subTest("outList check"):
            self.assertEqual(outList, expList)
        with self.subTest("errorCode check"):
            self.assertEqual(errorCode, expError)

        return (outName==expName and outList==expList and errorCode==expError)

    def print_failures(self, failBool, failList, numberRun):

        print("\ntest_occ_type_filter_random_inputs: " +
                str(numberRun) + " random inputs")
        if(failBool):
            print("\t\tThe following inputs failed")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for item in failList:
                print("\t" + str(item))
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        else:
            print("\tAll inputs passed")

    

    def run_occ_filter_test(self, failList, inputFile, randomFilter):

        testPass = True
        outNameExp, outListExp, errorCodeExp, testLog = testframe.get_test_json(
                inputFile,
                randomFilter
        )

        exp = testframe.ExpectedData()
        exp.level = testframe.get_levels(testLog)
        exp.count = testframe.get_log_count(testLog)

        if(exp.level['BYTECODE'] != 1):
            testframe.adjust_event_rule(inputFile, outListExp, randomFilter)

        exp.dataList = outListExp

        outNameR, outListR, errorCodeR = flaminglog.make_json(
                inputFile,
                randomFilter
        )

        results = testframe.ResultData()
        results.dataList = outListR

        #if the log file is invalid, e.g. only bytecode
        if(errorCodeExp != 0):

            #add tests for error code/msg here
            testPass = self.do_error_subtests(
                    outNameR,
                    outListR,
                    errorCodeR,
                    None,
                    None,
                    1004
            )

        else:
            checkHelper = testframe.CheckStruct(results, exp)
            levelCheck, dataCheck, countCheck, lenCheck = checkHelper.fullCheck()

            #keeps track of which filters failed
            boolList = [levelCheck, dataCheck, countCheck, lenCheck]
            for item in boolList:
                if not item:
                    testPass = False
                    failList.append(randomFilter.copy())

            self.do_sub_tests(
                    results,
                    exp,
                    countCheck,
                    levelCheck,
                    dataCheck,
                    lenCheck
            )

        return testPass

    def test_base_functionality(self):

        testLog = 'apitests/TestLogs/mainlog2.txt'
        verifiedJson = 'apitests/VerifiedJSON/verifiedmainlog2.json'


        exp = testframe.ExpectedData()

        exp.count = {
                'EVENT':9,
                'RULE':5,
                'RULEVM':5,
                'BYTECODE':90,
                'CMDVM':12,
                'CMD':9,
                'VAR_MOD':8
        }
       
        exp.level = {
                'EVENT':1,
                'RULE':2,
                'RULEVM':3,
                'BYTECODE':4,
                'CMDVM':5,
                'CMD':6,
                'VAR_MOD':5
        }
 
        with open(verifiedJson, 'r') as f:
            exp.dataList = json.load(f)


        outName, outList, errorCode = flaminglog.make_json(testLog)
        results = testframe.ResultData()
        results.dataList = outList

        checkHelper = testframe.CheckStruct(results, exp)
        levelCheck, dataCheck, countCheck, lenCheck = checkHelper.fullCheck()

        self.do_sub_tests(
                results,
                exp,
                countCheck,
                levelCheck,
                dataCheck,
                lenCheck
        )




    def test_occ_type_filter_random_inputs(self):

        failList = []
        anyFail = False
        for i in range(0, int(self.RUNNUMBER)):


            randomFilter = testframe.get_random_filter()
            testPass = self.run_occ_filter_test(
                    failList, 
                    self.INPUTFILE,
                    randomFilter
            )

            if not testPass:
                anyFail = True

        if(self.VERBOSITY >= 2):
            self.print_failures(anyFail, failList, self.RUNNUMBER)

    def test_occ_filter_single_input(self):

        """This test should be used to debug the API when it fails any of the
        random filter tests"""

        filterList = [
                'EVENT',
                'RULE',
                'RULEVM', 
                'BYTECODE',
                'CMDVM', 
                'CMD',
                'VAR_MOD'
        ]
        failList = []
        self.run_occ_filter_test(failList, self.INPUTFILE, filterList)


    def test_bytecode_only_trace(self):

        testfile = 'apitests/TestLogs/only_bytecode_trace.txt'
        outName, outList, errorCode = flaminglog.make_json(testfile)
        
        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1004
        )


    def test_empty_file(self):
       
        testfile = 'apitests/TestLogs/empty.txt'
        outName, outList, errorCode = flaminglog.make_json(testfile)

        with self.subTest("Length of output List"):
            self.assertEqual(len(outList), 0)

        with open(outName, 'r') as f:
            fileList = json.load(f)

        with self.subTest("Length of output file"):
            self.assertEqual(len(fileList), 0)

    def test_missing_entry_event(self):

        testFile = 'apitests/TestLogs/missing_entry_event.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_entry_rule(self):

        testFile = 'apitests/TestLogs/missing_entry_rule.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_entry_rulevm(self):

        testFile = 'apitests/TestLogs/missing_entry_rulevm.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )
        
    def test_missing_entry_cmdvm(self):

        testFile = 'apitests/TestLogs/missing_entry_cmdvm.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_entry_cmd(self):

        testFile = 'apitests/TestLogs/missing_entry_cmd.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_exit_event(self):
        
        testFile = 'apitests/TestLogs/missing_exit_event.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_exit_rule(self):
        
        testFile = 'apitests/TestLogs/missing_exit_rule.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_exit_rulevm(self):
        
        testFile = 'apitests/TestLogs/missing_exit_rulevm.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_exit_cmdvm(self):
        
        testFile = 'apitests/TestLogs/missing_exit_cmdvm.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_missing_exit_cmd(self):
        
        testFile = 'apitests/TestLogs/missing_exit_cmd.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1000
        )

    def test_event_found_low(self):
        testFile = 'apitests/TestLogs/event_lower.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_rule_found_low(self):
        testFile = 'apitests/TestLogs/rule_lower.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_rulevm_found_low(self):
        testFile = 'apitests/TestLogs/rulevm_lower.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_bytecode_found_low(self):
        testFile = 'apitests/TestLogs/bytecode_lower.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_cmdvm_found_low(self):
        testFile = 'apitests/TestLogs/cmdvm_lower.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_varmod_found_low(self):
        testFile = 'apitests/TestLogs/varmod_lower.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_rule_found_high(self):
        testFile = 'apitests/TestLogs/rule_higher.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_rulevm_found_high(self):
        testFile = 'apitests/TestLogs/rulevm_higher.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_bytecode_found_high(self):
        testFile = 'apitests/TestLogs/bytecode_higher.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_cmdvm_found_high(self):
        testFile = 'apitests/TestLogs/cmdvm_higher.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_cmd_found_high(self):
        testFile = 'apitests/TestLogs/cmd_higher.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_varmod_found_high(self):
        testFile = 'apitests/TestLogs/varmod_higher.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1001
        )

    def test_too_many_fields(self):
        testFile = 'apitests/TestLogs/too_many_fields.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)


        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1002
        )

    def test_too_few_fields(self):
        testFile = 'apitests/TestLogs/too_few_fields.txt'
        outName, outList, errorCode = flaminglog.make_json(testFile)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1003
        )

    def test_file_not_found(self):
        testFile = 'apitests/TestLogs/does_not_exist.txt'

        with self.assertRaises(Exception) as context:
            outName, outList, errorCode = flaminglog.make_json(testFile)
        errstr = ':was not found'
        self.assertTrue(errstr in str(context.exception))


    def test_invalid_occ_list(self):
        testFile = 'apitests/TestLogs/rawlog.txt'
        filterList = ['EVENT', 'RULE', 'RULEVM', 'INVALID']
        with self.assertRaises(Exception) as context:
            outName, outList, errorCode = flaminglog.make_json(
                    testFile,
                    filterList
            )
        errstr = ':is not a valid entry in wantedOccList'
        self.assertTrue(errstr in str(context.exception))

    def test_bytecode_top_level(self):
        testFile = 'apitests/TestLogs/rawlog.txt'
        filterList = ['BYTECODE', 'CMDVM', 'CMD']
        outName, outList, errorCode = flaminglog.make_json(testFile, filterList)

        self.do_error_subtests(
                outName,
                outList,
                errorCode,
                None,
                None,
                1004
        )

    def test_invalid_type_input(self):
        testFile = 'apitests/TestLogs/rawlog.txt'
        with self.assertRaises(Exception) as context:
            outName, outList, errorCode = flaminglog.make_json(testFile, 2)
        errstr = "object is not of type list or str:"
        self.assertTrue(errstr in str(context.exception))

if __name__ == '__main__':

    unittest.main()












