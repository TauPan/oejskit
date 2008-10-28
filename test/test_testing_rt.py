import py
import sys, os

import jskit.testing
from jskit.testing import InBrowserSupport

class TryInBrowser(InBrowserSupport):
    from jskit.tweb2 import TWeb2ServerSide as ServerSide

TryInBrowser.install(globals())

class BrowserTests(BrowserTestClass):

    def test_simple(self):
        send = self.browser.send
        res = self.browser.send('InBrowserTesting.result(42)')
        assert res == 42

    def test_open_helper(self):
        send = self.browser.send        
        res = send('InBrowserTesting.open("/browser_testing/rt/abc.txt")',
                   discrim="/browser_testing/rt/abc.txt")
        assert 'panel' in res
        n = res['panel']
        res = send('InBrowserTesting.open("/browser_testing/rt/abc.txt")',
                   discrim="/browser_testing/rt/abc.txt")
        assert res['panel'] == n

    def test_controller_open(self):
        browser = self.browser
        
        def root(environ, start_response):
            start_response('200 OK', [('content-type', 'text/plain')])
            return  ['my-root']

        class Controller(jskit.testing.BrowserController):
            wsgiEndpoints = {'/': root}

        controller = Controller()
        controller.browser  = browser
        controller.setupBag = jskit.testing.SetupBag(self, controller)

        pg = controller.open('/')
        scrapePanel = 'InBrowserTesting.result(scrapeText(document.getElementById("panel-frame-%d").contentWindow.document))' % pg.index
        text = browser.send(scrapePanel)
        assert text == "my-root"      

class TestFirefox(BrowserTests):
    browserKind = "firefox"
