import py
from oejskit.testing import BrowserTestClass, jstests_suite

class AFuncsTests(BrowserTestClass):

    @jstests_suite('test_afuncs.js')
    def test_inbrowser(self):
        return

class TestAFuncsFirefox(AFuncsTests):
    jstests_browser_kind = "firefox"

#class TestAFuncsIExplore(AFuncsTests):
#    jstests_browser_kind = "iexplore"        

#class TestAFuncsSafari(AFuncsTests):
#    jstests_browser_kind = "safari"
