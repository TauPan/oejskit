import py
import sys, os

import oejskit.testing
from oejskit.testing import BrowserTestClass, JsFailed


class BrowserTests(BrowserTestClass):

    def test_simple(self):
        send = self.browser.send
        res = self.browser.send('InBrowserTesting.result(42)')
        assert res == 42

    def test_open_helper(self):
        res = self.send('InBrowserTesting.open("/browser_testing/rt/abc.txt")',
                   discrim="/browser_testing/rt/abc.txt")
        assert 'panel' in res
        n = res['panel']
        res = self.send('InBrowserTesting.open("/browser_testing/rt/abc.txt")',
                   discrim="/browser_testing/rt/abc.txt")
        assert res['panel'] == n

    def test_open(self):
        browser = self.browser
        
        def root(environ, start_response):
            start_response('200 OK', [('content-type', 'text/plain')])
            return  ['my-root']

        class Controller(oejskit.testing.BrowserController):
            wsgiEndpoints = {'/': root}

        controller = Controller()
        controller.browser  = browser
        controller.setupBag = oejskit.testing.SetupBag(self, controller)

        pg = controller.open('/')
        scrapePanel = 'InBrowserTesting.result(scrapeText(document.getElementById("panel-frame-%d").contentWindow.document))' % pg.index
        text = browser.send(scrapePanel)
        assert text == "my-root"

    def test_eval(self):
        pg = self.open('/browser_testing/load/test/examples/test_eval_example.js')
        res = pg.eval("foo()")
        assert res == "foo"

        py.test.raises(JsFailed, pg.eval, "bar()")

    def test_travel(self):
        pg = self.open('/test/examples/test_form.html')

        res = pg.travel("document.forms['travel'].submit()")
        assert res == 'reloaded'

        title = pg.eval("document.title")
        assert title == "DEST"

    def test_takes(self):
        pg = self.open('/test/examples/test_form.html', take="a")

        res = pg.travel("document.forms['travel'].submit()")
        assert res == 'reloaded'

        title = pg.eval("document.title")
        assert title == "DEST"

        pg = self.open('/test/examples/test_form.html', take="b")

        title = pg.eval("document.title")
        assert title == "FORM"

class TestFirefox(BrowserTests):
    jstests_browser_kind = "firefox"

#class TestIExplore(BrowserTests):
#    jstests_browser_kind = "iexplore"

#class TestSafari(BrowserTests):
#    jstests_browser_kind = "safari"

# ________________________________________________________________

class RunningTestTests(BrowserTestClass):

    def classify(self, results):
        passed = {}
        failed = {}
        for outcome in results:
            if outcome['result']:
                passed[outcome['name']] = None
            else:
                failed[outcome['name']] = outcome['diag']
        return passed, failed

    def test_new_simple_setup(self):
        result = self.send('InBrowserTesting.collectTests("/test/examples/test_new_simple.html")',
                   discrim="/test/examples/test_new_simple.html@collect")
        assert result == sorted(['test_is_fail_1', 'test_is_fail_2', 'test_is_ok',
                                 'test_isDeeply_fail', 'test_isDeeply_ok',
                                 'test_ok_fail', 'test_ok_ok'])
        
    def test_new_simple_runOne(self):
        result = self.send('InBrowserTesting.collectTests("/test/examples/test_new_simple.html")',
                         discrim="/test/examples/test_new_simple.html@collect")
        assert len(result)  == 7

        result = self.send("""InBrowserTesting.runOneTest("/test/examples/test_new_simple.html",
                                                       "test_ok_ok", 1)""",
                         discrim="/test/examples/test_new_simple.html@1")

        assert result['name'] == "test_ok_ok"
        assert result['result']

    def test_new_simple_run(self):
        names = self.send('InBrowserTesting.collectTests("/test/examples/test_new_simple.html")',
                         discrim="/test/examples/test_new_simple.html@collect")
        assert len(names)  == 7


        outcomes = []
        for n, name in enumerate(names):
            result = self.send('InBrowserTesting.runOneTest("/test/examples/test_new_simple.html", %r, %d)' %
                            (str(name), n), discrim="/test/examples/test_new_simple.html@%d" % n)
            outcomes.append(result)
        passed, failed = self.classify(outcomes)
        assert sorted(passed.keys()) == sorted([name for name in names
                                                     if name.endswith('_ok')])
        assert len(failed)+len(passed) == len(names)

    def test_new_exception_run(self):
        names = self.send('InBrowserTesting.collectTests("/test/examples/test_new_exception.html")',
                         discrim="/test/examples/test_new_exception.html@collect")
        assert names == ['test_throw']

        result = self.send("""InBrowserTesting.runOneTest("/test/examples/test_new_exception.html",
                           "test_throw", 1)""",
                         discrim="/test/examples/test_new_exception.html@1")

        assert result['name'] == "test_throw"
        assert not result['result']

    def test_new_later_run(self):
        names = self.send('InBrowserTesting.collectTests("/test/examples/test_new_later.html")',
                         discrim="/test/examples/test_new_later.html@collect")
        assert len(names)  == 2

        outcomes = []
        for n, name in enumerate(names):
            result = self.send('InBrowserTesting.runOneTest("/test/examples/test_new_later.html", %r, %d)' %
                            (str(name), n), discrim="/test/examples/test_new_later.html@%d" % n)
            outcomes.append(result)
        passed, failed = self.classify(outcomes)
        assert passed.keys() == ['test_later']
        assert failed.keys() == ['test_later_exc']

    def test_new_leak_runOne(self):
        result = self.send('InBrowserTesting.collectTests("/test/examples/test_new_leak.html")',
                    discrim="/test/examples/test_new_leak.html@collect")
        assert len(result)  == 1

        result = self.send("""InBrowserTesting.runOneTest("/test/examples/test_new_leak.html",
                              "test_leak", 1)""",
                         discrim="/test/examples/test_new_leak.html@1")

        assert result['name'] == "test_leak"
        assert result['result']
        expected = ['LEAK']
        if self.jstests_browser_kind == 'iexplore':
            expected = [] # name leak detection is not attempted on IE :(
        assert result['leakedNames'] == expected

    def test_gather(self):
        b = self.browser
        res, runner = b._gatherTests("/test/examples/test_inBrowser.html",
                                     self.setupBag)
        assert res == ['test_failure', 'test_success']
        failed = False
        runner._runTest('test_success', None, None)

        failure = py.test.raises(JsFailed, runner._runTest, 'test_failure',
                                                             None, None)
        jsfailed = failure.value
        assert jsfailed.name == 'test_failure'
        assert jsfailed.msg.startswith("FAILED: 2 == 1")

    def test_load(self):
        self.runTests("/browser_testing/load/test/examples/test_load.js")

    def test_sanity(self):
        res = self.send('InBrowserTesting.result("end")')
        assert res == "end"

class TestRunningTestFirefox(RunningTestTests):
    jstests_browser_kind = "firefox"

#class TestRunningTestIExplore(RunningTestTests):
#    jstests_browser_kind = "iexplore"        

#class TestRunningTestSafari(RunningTestTests):
#    jstests_browser_kind = "safari"

