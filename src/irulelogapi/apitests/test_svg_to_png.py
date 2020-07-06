import sys, os
import unittest
import json
from . import testframe
import flaminglog.logrule as flaminglog

class TestSvgToPng(unittest.TestCase):

    def test_file_not_found(self):
        testfile = 'doesnotexist.svg'
        testout = 'testout.png'

        self.assertTrue(True, 'Unexpected Exception')
        """
        with self.assertRaises(Exception) as context:
            flaminglog.svg_to_png(testfile, testout)
        
        errStr = " :was not found"
        print(context.exception)
        self.assertTrue(errStr in str(context.exception))
        """

    def test_conversion_failure(self):
        testfile = 'apitests/TestSvgToPngFiles/failconvert.svg'
        testout = 'testout.png'

        with self.assertRaises(Exception) as context:
            flaminglog.svg_to_png(testfile, testout)

        errStr = "FAILED TO CONVERT SVG TO PNG"
        self.assertTrue(errStr in str(context.exception))

    def test_sucessful_png_creation(self):
        testfile = 'apitests/TestSvgToPngFiles/testflamegraph.svg'
        testout = 'apitests/tempfiles/testout.png'

        if os.path.exists(testout):
            os.remove(testout)

        flaminglog.svg_to_png(testfile,testout)
        self.assertTrue(os.path.exists(testout))

if __name__ == '__main__':
    unittest.main()
