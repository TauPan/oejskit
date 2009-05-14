import py
from oejskit.testing import BrowserTestClass, inBrowser

class UtilsTests(BrowserTestClass):

    @inBrowser
    def test_inbrowser(self):
        return self.gatherTests("/browser_testing/load/test/test_utils.js")


class TestUtilsFirefox(UtilsTests):
    jstests_browser_kind = "firefox"

#class TestUtilsIExplore(UtilsTests):
#    jstests_browser_kind = "iexplore"        

#class TestUtilsSafari(UtilsTests):
#    jstests_browser_kind = "safari"
