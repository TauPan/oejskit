import py
from jskit.testing import InBrowserSupport, inBrowser

class TryInBrowser(InBrowserSupport):
    from jskit.tweb2 import TWeb2ServerSide as ServerSide

TryInBrowser.install(globals())

class UtilsTests(BrowserTestClass):

    @inBrowser
    def test_inbrowser(self):
        return self.gatherTests("/browser_testing/load/test/test_utils.js")


class TestUtilsFirefox(UtilsTests):
    browserKind = "firefox"

class TestUtilsSafari(UtilsTests):
    browserKind = "safari"
