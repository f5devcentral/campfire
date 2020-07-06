import sys, os
import unittest
import json
from . import testframe
import flaminglog.logrule as flaminglog

class TestMakeSvg(unittest.TestCase):
        
    INPUTFILE1 = 'apitests/TestLogs/rawlog.txt'
    INPUTFILE2 = 'apitests/TestLogs/rawlog2.txt'

    def test_svg_was_created(self):
        outName, outList, errorCode = flaminglog.make_json(self.INPUTFILE1)
        exitCode, fileDict = flaminglog.make_svg(outList)
        self.assertTrue(os.path.exists('static/myflame1Combined.svg')) 
        self.assertTrue(os.path.exists('static/myflame1Separate.svg')) 
        

    def test_all_svgs_were_created_diff(self):
        outName1, outList1, errorCode1 = flaminglog.make_json(self.INPUTFILE1)
        outName2, outList2, errorCode2 = flaminglog.make_json(self.INPUTFILE2)
        exitCode, fileDict = flaminglog.make_svg(outList1, outList2)

        for key in fileDict:
            self.assertTrue(os.path.exists(key)) 

    def test_expected_outputs(self):
        outName, outList, errorCode = flaminglog.make_json(self.INPUTFILE1)
        exitCode, fileDict = flaminglog.make_svg(outList)
        self.assertTrue(exitCode, "exitCode is not True")

        for key in fileDict:
            if(key == 'static/myflame1Combined.svg' or key == 'static/myflame1Separate.svg'):
                self.assertTrue(fileDict[key] is not None)
            else:
                self.assertTrue(fileDict[key] is None)


    def test_expected_outputs_diff(self):
        outName1, outList1, errorCode1 = flaminglog.make_json(self.INPUTFILE1)
        outName2, outList2, errorCode2 = flaminglog.make_json(self.INPUTFILE2)
        exitCode, fileDict = flaminglog.make_svg(outList1, outList2)
        self.assertTrue(exitCode, "exitCode is not True")

        for key in fileDict:
            self.assertTrue(fileDict[key] is not None)


    def test_all_occurrences_in_svg(self):

        outName, outList, errorCode = flaminglog.make_json(self.INPUTFILE1)
        exitCode, fileDict = flaminglog.make_svg(outList)

        rList = testframe.get_all_occ_names(outList)
        resultBoolCom = testframe.check_names_in_svg(rList, 'static/myflame1Combined.svg')
        resultBoolSep = testframe.check_names_in_svg(rList, 'static/myflame1Separate.svg')

        self.assertTrue(resultBoolSep, 
                "Not all occurrences were found in separate svg file")
        self.assertTrue(resultBoolCom, 
                "Not all occurrences were found in combined svg file")

    def test_all_occurrences_in_svgs_diff(self):

        outName1, outList1, errorCode1 = flaminglog.make_json(self.INPUTFILE1)
        outName2, outList2, errorCode2 = flaminglog.make_json(self.INPUTFILE2)
        exitCode, fileDict = flaminglog.make_svg(outList1, outList2)

        rList1 = testframe.get_all_occ_names(outList1)
        rList2 = testframe.get_all_occ_names(outList2)

        file1List = [
                'static/myflame1Combined.svg',
                'static/myflame1Separate.svg',
                'static/diff1.svg'
        ]

        file2List = [
                'static/myflame2Combined.svg',
                'static/myflame2Separate.svg',
                'static/diff2.svg'
        ]

        for item in file1List:
            resultBool = testframe.check_names_in_svg(rList1, item)
            self.assertTrue(resultBool, 
                    "Not all occurrences were found in" + item)

        for item in file2List:
            resultBool = testframe.check_names_in_svg(rList2, item)
            self.assertTrue(resultBool, 
                    "Not all occurrences were found in" + item)


    def test_input_not_a_list(self):
        outList = "this is not a list"
        with self.assertRaises(Exception) as context:
            exitCode, fileDict = flaminglog.make_svg(outList)
        errStr = "Passed value must be a list"
        self.assertTrue(errStr in str(context.exception))

    def test_second_input_not_a_list(self):
        outList1 = []
        outList2 = "Not LIST"
        with self.assertRaises(Exception) as context:
            exitCode, fileDict = flaminglog.make_svg(outList1, outList2)
        errStr = "Passed value must be a list"
        self.assertTrue(errStr in str(context.exception))

    def test_empty_input_list(self):
        outList = []
        exitCode, fileDict = flaminglog.make_svg(outList)
        self.assertFalse(exitCode)
        emptyMsg = "Failed to create FlameGraph"
        self.assertTrue(emptyMsg in fileDict['static/myflame1Combined.svg'])
        self.assertTrue(emptyMsg in fileDict['static/myflame1Separate.svg'])

    def test_empty_input_list_diff(self):
        outList1 = []
        outList2 = []
        exitCode, fileDict = flaminglog.make_svg(outList1, outList2)
        self.assertFalse(exitCode)
        emptyMsg = "Failed to create FlameGraph"

        for key in fileDict:
            self.assertTrue(emptyMsg in fileDict[key])


if __name__ == '__main__':

    TestMakeSvg.INPUTFILE1 = os.environ.get(
            'TEST_INPUT_FILE1',
            TestMakeSvg.INPUTFILE1
    )

    TestMakeSvg.INPUTFILE2 = os.environ.get(
            'TEST_INPUT_FILE2',
            TestMakeSvg.INPUTFILE2
    )

    unittest.main()
