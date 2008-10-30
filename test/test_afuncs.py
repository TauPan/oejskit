import py
from jskit.testing import InBrowserSupport, inBrowser

class TryInBrowser(InBrowserSupport):
    from jskit.tweb2 import TWeb2ServerSide as ServerSide

TryInBrowser.install(globals())

class AFuncsTests(BrowserTestClass):

    @inBrowser
    def test_inbrowser(self):
        return self.gatherTests("/browser_testing/load/test/test_afuncs.js")


class TestAFuncsFirefox(AFuncsTests):
    browserKind = "firefox"

class TestAFuncsSafari(AFuncsTests):
    browserKind = "safari"
