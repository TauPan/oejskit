import py
import sys, os

from jskit.testing import InBrowserSupport

class TryInBrowser(InBrowserSupport):
    from jskit.tweb2 import TWeb2ServerSide as ServerSide

TryInBrowser.install(globals())

class BrowserTests(BrowserTestClass):

    def test_simple(self):
        res = self.browser.send('InBrowserTesting.result(42)')
        assert res == 42

class TestFirefox(BrowserTests):
    browserKind = "firefox"
