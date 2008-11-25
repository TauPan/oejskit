import py
import sys, os

try:
    py.test.fail("")
except Exception, e:
    Failed = e.__class__

import jskit.testing
from jskit.testing import InBrowserSupport, inBrowser

class TryInBrowser(InBrowserSupport):
    from jskit.tweb2 import TWeb2ServerSide as ServerSide

TryInBrowser.install(globals())


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

        class Controller(jskit.testing.BrowserController):
            wsgiEndpoints = {'/': root}

        controller = Controller()
        controller.browser  = browser
        controller.setupBag = jskit.testing.SetupBag(self, controller)

        pg = controller.open('/')
        scrapePanel = 'InBrowserTesting.result(scrapeText(document.getElementById("panel-frame-%d").contentWindow.document))' % pg.index
        text = browser.send(scrapePanel)
        assert text == "my-root"

    def test_eval(self):
        pg = self.open('/browser_testing/load/test/examples/test_eval_example.js')
        res = pg.eval("foo()")
        assert res == "foo"

        fail = False
        try:
            pg.eval("bar()")
        except Failed:
            t, v, tb = sys.exc_info()
            fail = True
        except:
            pass

        assert fail        

class TestFirefox(BrowserTests):
    browserKind = "firefox"

class TestSafari(BrowserTests):
    browserKind = "safari"

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
        if self.browserKind == 'iexplore':
            expected = [] # name leak detection is not attempted on IE :(
        assert result['leakedNames'] == expected

    def test_gather(self):
        res, runner = self.gatherTests("/test/examples/test_inBrowser.html")
        assert res == ['test_failure', 'test_success']
        failed = False
        runner.runOneTest('test_success')
        try:
            runner.runOneTest('test_failure')
        except Failed:
            failed = True
            t, v, tb = sys.exc_info()
            assert v.msg.startswith("test_failure: FAILED: 2 == 1")
        except:
            pass
        assert failed

    def test_inBrowser(self):
        @inBrowser
        def test_inBrowser():
            return self.gatherTests("/test/examples/test_inBrowser.html")

        resultGen = test_inBrowser() # generator

        passed = 0
        failed = 0

        for name, run, _ in resultGen:
            if 'test_success' in name:
                run(name)
                passed += 1
            else:
                try:
                    run(name)
                except Failed:
                    t, v, tb = sys.exc_info()
                    failed += 1
                    assert v.msg.startswith("test_failure: FAILED: 2 == 1")
                except:
                    pass

        assert passed == 1
        assert failed == 1

    # example
    #@inBrowser
    #def test_inBrowser(self):
    #    browser = self.browser
    #    return browser.gatherTests("/test/examples/test_inBrowser.html")

    def test_load(self):
        self.runTests("/browser_testing/load/test/examples/test_load.js")

    def test_sanity(self):
        res = self.send('InBrowserTesting.result("end")')
        assert res == "end"

class TestRunningTestFirefox(RunningTestTests):
    browserKind = "firefox"

class TestRunningTestSafari(RunningTestTests):
    browserKind = "safari"    

