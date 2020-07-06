import sys, os
import unittest
import json
import flaminglog.logrule as flaminglog
from . import testsuites

class TestCleanup(unittest.TestCase):

    def generate_files(self):
        testLog1 = 'apitests/TestLogs/beforelog.txt'
        testLog2 = 'apitests/TestLogs/afterlog.txt'

        outName1, outList1, err1 = flaminglog.make_json(testLog1)
        outName2, outList2, err2 = flaminglog.make_json(testLog2)

        exitBool, fileDict = flaminglog.make_svg(outList1, outList2)

    def test_multiple_sequential_calls(self):
        #just makes sure no exception is thrown if cleanup is called twice
        self.generate_files()
        try:
            flaminglog.cleanup()
            flaminglog.cleanup()
        except:
            self.fail('Sequential calls of cleanup cause an exception.')

    def test_all_files_deleted(self):
       
        #generate files to delete
        self.generate_files()
        flaminglog.cleanup()

        filesToDelete = [
                'static/myfold1Com.folded',
                'static/myfold1Sep.folded',
                'static/myfold2Com.folded',
                'static/myfold2Sep.folded',
                'static/halfFold.folded',
                'static/myflame1Combined.svg',
                'static/myflame1Separate.svg',
                'static/myflame2Combined.svg',
                'static/myflame2Separate.svg',
                'static/diff1.svg',
                'static/diff2.svg',
                'static/onlydiff.svg',
                'static/plog.txt'
        ]

        #makes sure all files in StructLogs/ were deleted
        self.assertTrue(len(os.listdir('StructLogs/')) == 0)

        for myfile in filesToDelete:
            if(os.path.exists(myfile)):
                errMsg = myfile + " should have been deleted."
                self.assertTrue(False, errMsg)

if __name__ == '__main__':

    unittest.main()
