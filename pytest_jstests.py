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

class JsTestSuite(py.test.collect.Collector):
    # xxx sorting

    def __init__(self, name, parent):
        super(JsTestSuite, self).__init__(name, parent)
        self.obj = getattr(self.parent.obj, name)
        
    def collect(self):
        from oejskit.testing import giveBrowser        
        obj = self.obj
        browser, setupBag = giveBrowser(self.parent.parent) # XXX assumption
        url = obj._jstests_suite_url
        if not url.startswith('/'):
            url = "/browser_testing/load/test/%s" % url
        names, runner = browser._gatherTests(url, setupBag)
        # xxx root, funcargs for original function
        l = []
        for jstest in names:
            name = "%s[%s]" %(self.name, jstest)
            function = self.parent.Function(name=name, parent=self, 
                                            args=(jstest, None, None),
                                            callobj=runner._runTest)
            l.append(function)
        return l 

