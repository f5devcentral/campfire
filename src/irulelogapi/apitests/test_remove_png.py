import sys, os
import unittest
import flaminglog.logrule as flaminglog

class TestRemovePngFiles(unittest.TestCase):

    def generate_files(self, folder = ''):
        
        testLog1 = 'apitests/TestLogs/beforelog.txt'
        testLog2 = 'apitests/TestLogs/afterlog.txt'

        outName1, outList1, err1 = flaminglog.make_json(testLog1)
        outName2, outList2, err2 = flaminglog.make_json(testLog2)

        exitBool, fileDict = flaminglog.make_svg(outList1, outList2)

        for key in fileDict:
            if key is not None:
                flaminglog.svg_to_png(key, key[:-3]+'png')

    def test_no_folder_input(self):

       self.generate_files()

       flaminglog.remove_png_files()

       for myfile in os.listdir('.'):
           if(myfile.endswith('.png')):
                errMsg = myfile + ' should have been deleted.'
                self.assertTrue(False, errMsg)

    def test_folder_input(self):

       self.generate_files('static/')

       flaminglog.remove_png_files('static')

       for myfile in os.listdir('static/'):
           if(myfile.endswith('.png')):
                errMsg = myfile + ' should have been deleted.'
                self.assertTrue(False, errMsg)


    def test_invalid_folder(self):
        folder = 'invalid'

        with self.assertRaises(Exception) as context:
            flaminglog.remove_png_files('badfolder')

        errStr = "[Errno 2] No such file or directory: 'badfolder/'"
        self.assertTrue(errStr in str(context.exception))



if __name__ == '__main__':

    unittest.main()








