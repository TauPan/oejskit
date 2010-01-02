#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import py, os, sys


# hooks

jstests_setup = None
from oejskit import util

jstests_cmdline_browser_specs = {
    'any': util.any_browser()
}

def cmdline_browser_spec(option, optstr, value, parser):
    name, choices = value.split('=')
    choices = choices.split(',')
    jstests_cmdline_browser_specs[name] = choices

def pytest_addoption(parser):
    group = parser.getgroup("jstests", "oejskit test suite options")
    group.addoption(
        "--jstests-reuse-browser-windows", action="store_true",
        dest="jstests_reuse_browser_windows",
        help="don't use one tab/windows per test file"
        )
    group.addoption(
        "--jstests-browser-spec", action="callback", type="string",
        callback=cmdline_browser_spec,
        help="define browser specs like: supported=firefox,safari"
        )
    group.addoption(
        "--jstests-server-side", action="store",
        dest="jstests_server_side",
        type="string",
        default="oejskit.wsgi.WSGIServerSide"
        )

def pytest_pycollect_makeitem(collector, name, obj):
    if (collector.classnamefilter(name)) and \
        py.std.inspect.isclass(obj) and \
        hasattr(obj, 'jstests_browser_kind'):
        browserKind = obj.jstests_browser_kind
        return ClassWithBrowserCollector(name,
                                         parent=collector,
                                         browserKind=browserKind)
    if hasattr(obj, '_jstests_suite_url'):
        return JsTestSuite(name, parent=collector)
    return None

class RunState:

    def __init__(self, collector):
        self.collector = collector

    def getglobal(self, name):
        try:
            return self.collector.config.getvalue(name)
        except KeyError:
            raise AttributeError(name)

    def getscoped(self, name):
        pluginmanager = self.collector.config.pluginmanager
        plugins = pluginmanager.getplugins()
        if hasattr(self.collector, 'obj'):
            plugins.append(self.collector.obj)
        values = pluginmanager.listattr(attrname=name, plugins=plugins)
        values = [value for value in values if value is not None]
        if values:
            return values[-1]
        return None

    @property
    def testdir(self):
        if hasattr(self.collector, 'obj'):
            return os.path.dirname(self.collector.obj.__file__)
        else:
            return str(self.collector.fspath.dirpath())

    @property
    def testname(self):
        if hasattr(self.collector, 'obj'):        
            return self.collector.obj.__name__
        else:
            return self.collector.name
        

_run = {}

def get_state(item, collect=False):
    collector = item.getparent((py.test.collect.Module, JsFile))
    try:
        return _run[collector]
    except KeyError:
        pass
    _run[collector] = state = RunState(collector)
    if not collect:
        #print "ADD FINALIZER", os.getpid()
        #import traceback; traceback.print_stack()        
        collector.config._setupstate.addfinalizer(colitem=collector,
                                     finalizer=lambda: del_state(collector))
    return state

def del_state(item):
    collector = item.getparent((py.test.collect.Module, JsFile))    
    state = _run.pop(collector, None)
    if state:
        from oejskit.testing import cleanupBrowsers
        cleanupBrowsers(state)        

def pytest_collectstart(collector):
    if isinstance(collector, (py.test.collect.Module, JsFile)):
        get_state(collector, collect=True)

def pytest_collectreport(report):
    collector = report.collector
    if isinstance(collector, (py.test.collect.Module, JsFile)):
        del_state(collector)

def pytest_unconfigure(config):
    for colitem in _run.keys():
        del_state(colitem)

# jstest_*.js collection

def pytest_collect_file(path, parent):
    basename = path.basename
    if basename.startswith('jstest_') and basename.endswith('.js'):
        return JsFile(path, parent)
    return None

# ________________________________________________________________
# items

def give_browser(item, attach=True):
    from oejskit.testing import giveBrowser
    return giveBrowser(get_state(item), getattr(item, 'obj', None),
                                        item.browserKind,
                                        attach=attach)

def detach_browser(clsitem):
    from oejskit.testing import detachBrowser
    detachBrowser(clsitem.obj)

def expand_browsers(config, kind):
    from oejskit.testing import checkBrowser
    
    if kind is None:
        kind = 'any'

    # the command line takes precedence
    kinds = None
    try:
        kinds =  jstests_cmdline_browser_specs[kind]
    except KeyError:
        try:
            specs = config.getvalue('jstests_browser_specs')
        except KeyError:
            pass
        else:
            try:
                kinds = specs[kind]
            except KeyError:
                pass

    # assume kind identifies a single browser
    if kinds is None:
        kinds = [kind]

    return [kind for kind in kinds if checkBrowser(kind)] 

# collection

class BrowsersCollector(py.test.collect.Collector):
    Child = None
       
    def collect(self):
        l = []
        kinds = expand_browsers(self.config, self.browserKind)
        if not kinds:
            py.test.skip("no browser of kind %s" % self.browserKind)
        for kind in kinds:
            name = "[=%s]" % kind
            child = self.Child(name, self, kind)
            l.append(child)
        return l


class JsSuiteCollector(py.test.collect.Collector):
    _root = None

    def _collect(self, state_item, url):
        browser, setupBag = give_browser(state_item, attach=False)
        
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

# browser test classes collection
    
class ClassWithBrowser(py.test.collect.Class):

    def __init__(self, name, parent, browserKind):
        super(ClassWithBrowser, self).__init__(name, parent)
        self.obj = parent.obj
        self.browserKind = browserKind

    def setup(self):
        browser, setupBag = give_browser(self, attach=True)
        super(ClassWithBrowser, self).setup()

    def teardown(self):
        super(ClassWithBrowser, self).teardown()
        detach_browser(self)


class ClassWithBrowserCollector(BrowsersCollector):
    Child = ClassWithBrowser
    
    def __init__(self, name, parent, browserKind):
        super(ClassWithBrowserCollector, self).__init__(name, parent)
        self.obj = getattr(self.parent.obj, name)
        self.browserKind = browserKind

    def reportinfo(self):
        try:
            return self._fslineno, self.name
        except AttributeError:
            pass        
        fspath, lineno = py.code.getfslineno(self.obj)
        self._fslineno = fspath, lineno
        return fspath, lineno, self.name

class JsTestSuite(JsSuiteCollector):
    # this is a mixture between a collector, a setup method
    # and a function item
    
    def __init__(self, name, parent):
        super(JsTestSuite, self).__init__(name, parent)
        self.obj = getattr(self.parent.obj, name)
        self._root = None
        self.funcargs = {}

    def _getfslineno(self):
        try:
            return self._fslineno
        except AttributeError:
            pass
        self._fslineno = py.code.getfslineno(self.obj)
        return self._fslineno

    def reportinfo(self):
        fspath, lineno = self._getfslineno()
        return fspath, lineno, self.name

    def setup(self):
        self._root = None
        assert isinstance(self.parent, py.test.collect.Instance)
        self.parent.newinstance()
        self.obj = getattr(self.parent.obj, self.name)
        py.test.collect._fillfuncargs(self)
        self._root = self.obj(**self.funcargs)
            
    def teardown(self):
        super(JsTestSuite, self).teardown()
        self._root = None
        
    def collect(self):
        obj = self.obj
        clsitem = self.parent.parent
        assert isinstance(clsitem, py.test.collect.Class)
        url = obj._jstests_suite_url
        return self._collect(clsitem, url)


class JsTest(py.test.collect.Function):

    def reportinfo(self):
        fspath, lineno = self.parent._getfslineno()
        return fspath, lineno, self.getmodpath()

# js files

class JsFileSuite(JsSuiteCollector):

    def __init__(self, name, parent, browserKind):
        super(JsFileSuite, self).__init__(name, parent)
        self.browserKind = browserKind

    # accomodate JsTest/Function assumption
    obj = None
    
    def _getfslineno(self):
        return self.parent.fspath, 0
    # 

    def setup(self):
        browser, setupBag = give_browser(self, attach=False)
        super(JsFileSuite, self).setup()

    # nothing special to do in teardown

    def collect(self):
        url = self.parent.fspath.basename
        return self._collect(self, url)

class JsFile(py.test.collect.File, BrowsersCollector):
    Child = JsFileSuite

    def __init__(self, fspath, parent):
        super(JsFile, self).__init__(fspath, parent)
        self.browserKind = fspath.purebasename.split('_')[-1]

