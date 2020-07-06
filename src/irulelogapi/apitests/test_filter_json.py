import sys, os
import unittest
import json
from . import testframe
import flaminglog.logrule as flaminglog
import copy
import random

class TestFilterJson(unittest.TestCase):

    INPUTFILE = os.environ.get('TEST_INPUT_FILE', 'apitests/FilterTestJSON/mainlog2.txt')
    RUNNUMBER = int(os.environ.get('TEST_RUN_NUMBER', 1))
    VERBOSITY = int(os.environ.get('TEST_VERBOSITY', 2))
    

    def do_sub_tests(
            self,
            results,
            exp,
            countCheck,
            levelCheck,
            dataCheck,
            lenCheck,
            valueDict
        ):
        """
        Does the actual tests
        """
        countMsg = "FAILED: Count Incorrect\n"
        countMsg += "Filter Input: " + str(valueDict) + "\n"
        countMsg += "\tExpected: " + str(exp.count) + "\n"
        countMsg += "\tActual: " + str(results.count) + "\n"
        with self.subTest('Test Count'):
            self.assertTrue(countCheck, countMsg)

        dataMsg = "FAILED: Data Inconsistent\n"
        dataMsg += "Filter Input: " + str(valueDict) + "\n"
        dataMsg += "\tFailed Levels: " + str(results.dataFails)
        with self.subTest('Test Data'):
            self.assertTrue(dataCheck, dataMsg)

        levelMsg = "FAILED: Occurrence found outside expected level\n"
        levelMsg += "Filter Input: " + str(valueDict) + "\n"
        levelMsg += "\tFailed Levels: " + str(results.levelFails)
        with self.subTest('Test Occurrence Levels'):
            self.assertTrue(levelCheck, levelMsg)

        lenMsg = "FAILED: Actual and Expected have different amounts of data\n"
        lenMsg += "Filter Input: " + str(valueDict) + "\n"
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

    def print_failures(self, testName, failBool, failedInputs, runNumber):

        print("\n" + testName + ': ' + str(runNumber) + " random inputs")
        if(failBool):
            print("\t\tThe following inputs failed")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for item in failedInputs:

                print("-----------------")
                for key in item:
                    print("\t" + key + ': ' + str(item[key]))
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        else:
            print("\tAll inputs passed")


    def run_filter_macro(self, filterDict, dataList):
        for key in filterDict:
            if(key == 'irule'):
                for index, item in enumerate(filterDict[key]):
                    filterDict[key][index] = item[1:].replace('/','-')
            filterDict[key] = "['" + str(','.join(filterDict[key])) + "']"
        parseDict = flaminglog.parse_filter_dict(filterDict)
        resultList = flaminglog.run_multiple_filters(parseDict, dataList)

        return resultList


    def run_filters(self, valueDict, dataList):

        resultingList = copy.deepcopy(dataList)
        for key in valueDict:

            filterStrHeader = key + '=='
            filterStrList = []
            for valueStr in valueDict[key]:

                singleStr = filterStrHeader + valueStr
                singleStr = '(' + singleStr + ')'
                filterStrList.append(singleStr)

            finalFilterStr = '|'.join(filterStrList)
            
            #if no filter is applied for given field
            if(len(valueDict[key])==0):
                finalFilterStr = None
            resultingList = flaminglog.filter_json(
                    resultingList,
                    finalFilterStr
            )

        return resultingList


    def test_random_combos_with_macro(self):

        rawJsonFile, rawJsonList, errorCode = flaminglog.make_json(
                self.INPUTFILE
        )
        masterValueDict, realCombos = testframe.gather_filter_values(
                self.INPUTFILE
        )

        failedInputs = []
        anyFail = False
        for i in range(0,int(self.RUNNUMBER)):
            valueDict = testframe.get_random_combos(realCombos)
            #eventval can only handle 1 value
            #creates file to check filter output against
            verifiedJson, countDict, levelDict = testframe.make_verified_json(
                    self.INPUTFILE,
                    valueDict
            )

            #populate expected data structure
            exp = testframe.ExpectedData()
            exp.count = countDict
            exp.level = levelDict
            with open(verifiedJson, 'r') as f:
                exp.dataList = json.load(f)

            #runs the actual filter tests
            filteredList = self.run_filter_macro(valueDict, rawJsonList)

            #populate result data structure
            results = testframe.ResultData()
            results.dataList = filteredList
            #compare the output data and run test assertions
            checkHelper = testframe.CheckStruct(results, exp)
            levelCheck, dataCheck, countCheck, lenCheck = checkHelper.fullCheck()
            self.do_sub_tests(
                    results,
                    exp,
                    countCheck,
                    levelCheck,
                    dataCheck,
                    lenCheck,
                    valueDict
            )
            failBool = False
            checkList = [countCheck, levelCheck, dataCheck, lenCheck]
            for check in checkList:
                if(check==False):
                    failBool = True
                    anyFail = True

            if(failBool):
                failedInputs.append(valueDict)

        if(self.VERBOSITY >= 2):
            self.print_failures(
                    'test_random_combos_with_macro',
                    anyFail,
                    failedInputs,
                    self.RUNNUMBER
            )
        """
        print("\ttest_random_combos_with_macro: " + 
                str(self.RUNNUMBER) + " random inputs")
        if(anyFail):
            print("\t\tThe following inputs failed")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for item in failedInputs:

                print("-----------------")
                for key in item:
                    print("\t" + key + ': ' + str(item[key]))
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        else:
            print("\tAll inputs passed")
        """
    def test_single_input(self):

        rawJsonFile, rawJsonList, errorCode = flaminglog.make_json(
                self.INPUTFILE
        )
        masterValueDict, realCombos = testframe.gather_filter_values(
                self.INPUTFILE
        )

        valueDict = {
                'eventval':[],
                'irule':[],
                'remote':[],
                'local':[],
                'flow':[]
        }
   
       
        #creates file to check filter output against
        verifiedJson, countDict, levelDict = testframe.make_verified_json(
                self.INPUTFILE,
                valueDict
        )

        #populate expected data structure
        exp = testframe.ExpectedData()
        exp.count = countDict
        exp.level = levelDict
        with open(verifiedJson, 'r') as f:
            exp.dataList = json.load(f)

        #runs the actual filter tests
        filteredList = self.run_filters(valueDict, rawJsonList)

        #populate result data structure
        results = testframe.ResultData()
        results.dataList = filteredList
        
        #compare the output data and run test assertions
        checkHelper = testframe.CheckStruct(results, exp)
        levelCheck, dataCheck, countCheck, lenCheck = checkHelper.fullCheck()
        self.do_sub_tests(
                results,
                exp,
                countCheck,
                levelCheck,
                dataCheck,
                lenCheck,
                valueDict
        )
        if(self.VERBOSITY >=2):
            print("\ntest_single_input: modify this test to reproduce failures") 
            print("\t\tThe following input was tested")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for key in valueDict:
                print("\t" + key + ': ' + str(valueDict[key]))
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")





    def test_random_combos(self):

        rawJsonFile, rawJsonList, errorCode = flaminglog.make_json(
                self.INPUTFILE
        )
        masterValueDict, realCombos = testframe.gather_filter_values(
                self.INPUTFILE
        )
       
        failedInputs = []

        anyFail = False
        for i in range(0,int(self.RUNNUMBER)):
            valueDict = testframe.get_random_combos(realCombos)
       
           
            #creates file to check filter output against
            verifiedJson, countDict, levelDict = testframe.make_verified_json(
                    self.INPUTFILE,
                    valueDict
            )

            #populate expected data structure
            exp = testframe.ExpectedData()
            exp.count = countDict
            exp.level = levelDict
            with open(verifiedJson, 'r') as f:
                exp.dataList = json.load(f)

            #runs the actual filter tests
            filteredList = self.run_filters(valueDict, rawJsonList)

            #populate result data structure
            results = testframe.ResultData()
            results.dataList = filteredList

            #compare the output data and run test assertions
            checkHelper = testframe.CheckStruct(results, exp)
            levelCheck, dataCheck, countCheck, lenCheck = checkHelper.fullCheck()
            self.do_sub_tests(
                    results,
                    exp,
                    countCheck,
                    levelCheck,
                    dataCheck,
                    lenCheck,
                    valueDict
            )

            failBool = False
            checkList = [countCheck, levelCheck, dataCheck, lenCheck]
            for check in checkList:
                if(check==False):
                    failBool = True
                    anyFail = True

            if(failBool):
                failedInputs.append(valueDict)

        if(self.VERBOSITY >= 2):
            self.print_failures(
                    'test_random_combos',
                    anyFail,
                    failedInputs,
                    self.RUNNUMBER
            )


    def test_completely_random_combos(self):

        rawJsonFile, rawJsonList, errorCode = flaminglog.make_json(
                self.INPUTFILE
        )
        masterValueDict, realCombos = testframe.gather_filter_values(
                self.INPUTFILE
        )

        failedInputs = []

        anyFail = False
        for i in range(0,int(self.RUNNUMBER)):
            valueDict = testframe.get_random_filters(masterValueDict)
       
           
            #creates file to check filter output against
            verifiedJson, countDict, levelDict = testframe.make_verified_json(
                    self.INPUTFILE,
                    valueDict
            )

            #populate expected data structure
            exp = testframe.ExpectedData()
            exp.count = countDict
            exp.level = levelDict
            with open(verifiedJson, 'r') as f:
                exp.dataList = json.load(f)

            #runs the actual filter tests
            filteredList = self.run_filters(valueDict, rawJsonList)

            #populate result data structure
            results = testframe.ResultData()
            results.dataList = filteredList

            #compare the output data and run test assertions
            checkHelper = testframe.CheckStruct(results, exp)
            levelCheck, dataCheck, countCheck, lenCheck = checkHelper.fullCheck()
            self.do_sub_tests(
                    results,
                    exp,
                    countCheck,
                    levelCheck,
                    dataCheck,
                    lenCheck,
                    valueDict
            )

            failBool = False
            checkList = [countCheck, levelCheck, dataCheck, lenCheck]
            for check in checkList:
                if(check==False):
                    failBool = True
                    anyFail = True

            if(failBool):
                failedInputs.append(valueDict)

        if(self.VERBOSITY >= 2):
            self.print_failures(
                    'test_completely_random_combos',
                    anyFail,
                    failedInputs,
                    self.RUNNUMBER
            )
        """
        print("\ttest_completely_random_combos: " + 
                str(self.RUNNUMBER) + " random inputs")
        if(anyFail):
            print("\t\tThe following inputs failed")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for item in failedInputs:

                print("-----------------")
                for key in item:
                    print("\t" + key + ': ' + str(item[key]))
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        else:
            print("\tAll inputs passed")
        """

    def test_invalid_filter_string(self):

        rawJsonFile, rawJsonList, errorCode = flaminglog.make_json(
                self.INPUTFILE
        )

        invalidList = [
                '(eventval==val1',
                '(eVals==val2)',
                '(remote==10.2)%(remote==10.3)',
                '(local==80)',
                '(irule=beep)',
                '(flow==98-p-0)',
                '(remote==99:23)',
                '(flow==10.10.2:88:0-10.10.3:661)'
        ]

        for myStr in invalidList:
            failMsg = "Failed Str: " + myStr
            with self.assertRaises(Exception) as context:
                filteredList = flaminglog.filter_json(rawJsonList, myStr)
            errstr = 'INVALID FILTER STRING:'
            self.assertTrue(errstr in str(context.exception))

    def test_empty_input_file(self):
        testList = []
        filteredList = flaminglog.filter_json(testList)
        self.assertTrue(len(filteredList) == 0)

    def test_input_not_a_list(self):
        outList = "this is not a list"
        with self.assertRaises(Exception) as context:
            filteredList = flaminglog.filter_json(outList)
        errStr = "Passed value must be a list"
        self.assertTrue(errStr in str(context.exception))



if __name__ == '__main__':

    unittest.main()
