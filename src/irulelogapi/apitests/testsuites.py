import unittest
from . import test_make_json
from . import test_filter_json
from . import test_make_svg
from . import test_cleanup
from . import test_svg_to_png
from . import test_remove_png
from . import test_handle_error

def run_full_suite(verboseLevel=2):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromModule(test_make_json))
    suite.addTests(loader.loadTestsFromModule(test_filter_json))
    suite.addTests(loader.loadTestsFromModule(test_make_svg))
    suite.addTests(loader.loadTestsFromModule(test_svg_to_png))
    suite.addTests(loader.loadTestsFromModule(test_cleanup))
    suite.addTests(loader.loadTestsFromModule(test_remove_png))
    suite.addTests(loader.loadTestsFromModule(test_handle_error))
    unittest.TextTestRunner(verbosity=verboseLevel).run(suite)
