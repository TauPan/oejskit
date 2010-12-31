import unittest, sys, os
from oejskit import util
from oejskit.testing import giveBrowser, cleanupBrowsers, checkBrowser

NOT_THERE = object()

class JSTestSuite(unittest.TestSuite):

    jstests_browser_specs = None

    def getglobal(self, name):
        return getattr(self, name)

    def _expand_browser(self, kind):
        try:
            kinds = self.jstests_browser_specs[kind]
        except KeyError:
            kinds = [kind]
        return [kind for kind in kinds if checkBrowser(kind)]
            
    def __init__(self, js, root=None, browser_kind=None):
        self.testdir = os.path.dirname(sys._getframe(1).f_globals['__file__'])
        self.testname = js

        if root is None:
            root = lambda: None
            
        if self.jstests_browser_specs is None:
            self.jstests_browser_specs = {}
        if 'any' not in self.jstests_browser_specs:
            self.jstests_browser_specs['any'] = util.any_browser()

        tests = []

        if browser_kind is None:
            purebasename = os.path.splitext(os.path.basename(js))[0]
            browser_kind = purebasename.split('_')[-1]

        for kind in self._expand_browser(browser_kind):
            browser, setupBag = giveBrowser(self, self.__class__,
                                            kind, attach=False)

            names, runner = browser._gatherTests(js, setupBag)
            runner._the_root = NOT_THERE

            def makeRunTest(runner, jstest):
                def runTest():
                    if runner._the_root is NOT_THERE:
                        runner._the_root = root()
                    runner._runTest(jstest, runner._the_root, None)
                return runTest

            for jstest in names:
                runTest = makeRunTest(runner, jstest)
                descr = '%s[=%s][%s]' % (self.testname, kind, jstest)
                tests.append(unittest.FunctionTestCase(runTest,
                                                       description=descr))
            
        unittest.TestSuite.__init__(self, tests)

    def run(self, result):
        unittest.TestSuite.run(self, result)
        cleanupBrowsers(self)
