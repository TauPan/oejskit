import py
from oejskit.testing import InBrowserSupport, inBrowser

class TryInBrowser(InBrowserSupport):
    from oejskit.wsgi import WSGIServerSide as ServerSide

TryInBrowser.install(globals())


class AFuncsTests(BrowserTestClass):

    @inBrowser
    def test_inbrowser(self):
        return self.gatherTests("/browser_testing/load/test/test_afuncs.js")


class TestAFuncsFirefox(AFuncsTests):
    browserKind = "firefox"

class TestAFuncsIExplore(AFuncsTests):
    browserKind = "iexplore"        

class TestAFuncsSafari(AFuncsTests):
    browserKind = "safari"
