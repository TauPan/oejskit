import py
from oejskit.testing import BrowserTestClass, jstests_suite

class UtilsTests(BrowserTestClass):

    @jstests_suite('test_utils.js')
    def test_inbrowser(self):
        pass


class TestUtilsFirefox(UtilsTests):
    jstests_browser_kind = "firefox"

#class TestUtilsIExplore(UtilsTests):
#    jstests_browser_kind = "iexplore"        

#class TestUtilsSafari(UtilsTests):
#    jstests_browser_kind = "safari"
