import py
from jskit.testing import InBrowserSupport, inBrowser

class TryInBrowser(InBrowserSupport):
    from jskit.wsgi import WSGIServerSide as ServerSide

TryInBrowser.install(globals())


class UtilsTests(BrowserTestClass):

    @inBrowser
    def test_inbrowser(self):
        return self.gatherTests("/browser_testing/load/test/test_utils.js")


class TestUtilsFirefox(UtilsTests):
    browserKind = "firefox"

class TestUtilsIExplore(UtilsTests):
    browserKind = "iexplore"        

class TestUtilsSafari(UtilsTests):
    browserKind = "safari"
