#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import py
        

class JstestsPlugin(object):

    jstests_setup = None

    def pytest_addoption(self, parser):
        group = parser.addgroup("jstests", "oejskit test suite options")
        group.addoption(
            "--jstests-server-side", action="store",
            dest="jstests_server_side",
            type="string",
            default="oejskit.wsgi.WSGIServerSide"
            )
        group.addoption(
            "--jstests-reuse-browser-windows", action="store_true",
            dest="jstests_reuse_browser_windows",
            )

    def pytest_pycollect_obj(self, collector, name, obj):
        if (collector.classnamefilter(name)) and \
            py.std.inspect.isclass(obj) and \
            hasattr(obj, 'jstests_browser_kind'):
            return ClassWithBrowser(name, parent=collector)
        if hasattr(obj, '_jstests_suite_url'):
            return JsTestSuite(name, parent=collector)
        return None

    # xxx this really wants a teardown hook, both for --collectonly
    # and runs
    def pytest_collectreport(self, rep):
        if isinstance(rep.colitem, py.test.collect.Module):
            from oejskit.testing import cleanupBrowsers
            cleanupBrowsers(rep.colitem.obj.__dict__)


class ClassWithBrowser(py.test.collect.Class):

    def setup(self):
        from oejskit.testing import giveBrowser
        browser, setupBag = giveBrowser(self)
        self.obj.browser = browser
        self.obj.setupBag = setupBag
        super(py.test.collect.Class, self).setup()

# xxx too much duplication with the pylib itself

class JsTestSuite(py.test.collect.Collector):
    # this is a mixture between a collector, a setup method
    # and a function item (it makes sense but it's messy to implement
    # right now)

    def __init__(self, name, parent):
        super(JsTestSuite, self).__init__(name, parent)
        self.obj = getattr(self.parent.obj, name)
        self._root = None
        self._finalizers = []
        self._args = None
        self.funcargs = {}

    def _getfslineno(self):
        try:
            return self._fslineno
        except AttributeError:
            pass
        self._fslineno = py.code.getfslineno(self.obj)
        return self._fslineno

    # xxx
    def reportinfo(self):
        fspath, lineno = self._getfslineno()
        return fspath, lineno, self.name

    def _getsortvalue(self):
        return self.reportinfo()
    # /xxx

    def _getparent(self, cls): # xxx bad
        current = self
        while current and not isinstance(current, cls):
            current = current.parent
        return current 

    def setup(self):
        self._root = None
        assert isinstance(self.parent, py.test.collect.Instance)
        self.parent.newinstance()
        self.obj = getattr(self.parent.obj, self.name)
        from py.__.test.funcargs import fillfuncargs
        fillfuncargs(self)
        self._root = self.obj(**self.funcargs)
    
    def addfinalizer(self, func):
        self._finalizers.append(func)
        
    def teardown(self):
        finalizers = self._finalizers
        while finalizers:
            call = finalizers.pop()
            call()
        super(py.test.collect.Collector, self).teardown()
        self._root = None
        
    def collect(self):
        from oejskit.testing import giveBrowser        
        obj = self.obj
        clsitem = self.parent.parent
        assert isinstance(clsitem, py.test.collect.Class)
        browser, setupBag = giveBrowser(clsitem)
        url = obj._jstests_suite_url
        if not url.startswith('/'):
            url = "/browser_testing/load/test/%s" % url
        names, runner = browser._gatherTests(url, setupBag)

        def runTest(jstest):
            runner._runTest(jstest, self._root, None)
            
        l = []
        for jstest in names:
            name = "[%s]" % jstest
            function = JsTest(name=name, parent=self, 
                              args=(jstest,), callobj=runTest)
            l.append(function)
        return l

class JsTest(py.test.collect.Function):

    # xxx
    def reportinfo(self):
        fspath, lineno = self.parent._getfslineno()
        return fspath, lineno, self.getmodpath()

    def _getsortvalue(self):
        fspath, lineno = self.parent._getfslineno()
        return fspath, lineno, self.name
    # /xxx


