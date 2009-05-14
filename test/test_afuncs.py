import py
from oejskit.testing import BrowserTestClass, inBrowser

class AFuncsTests(BrowserTestClass):

    @inBrowser
    def test_inbrowser(self):
        return self.gatherTests("/browser_testing/load/test/test_afuncs.js")


class TestAFuncsFirefox(AFuncsTests):
    jstests_browser_kind = "firefox"

#class TestAFuncsIExplore(AFuncsTests):
#    jstests_browser_kind = "iexplore"        

#class TestAFuncsSafari(AFuncsTests):
#    jstests_browser_kind = "safari"
