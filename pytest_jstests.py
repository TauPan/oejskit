#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import py, os


# hooks

jstests_setup = None

jstests_cmdline_browser_specs = {
    'any': ['firefox'] # fallback
}

def cmdline_browser_spec(option, optstr, value, parser):
    name, choices = value.split('=')
    choices = choices.split(',')
    jstests_cmdline_browser_specs[name] = choices

def pytest_addoption(parser):
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
    group.addoption(
        "--jstests-browser-spec", action="callback", type="string",
        callback=cmdline_browser_spec
        )


def pytest_pycollect_obj(collector, name, obj):
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

    def __init__(self, modcol):
        self.modcol = modcol

    def getglobal(self, name):
        try:
            return self.modcol.config.getvalue(name)
        except KeyError:
            raise AttributeError(name)

    def getscoped(self, name):
        pluginmanager = self.modcol.config.pluginmanager
        plugins = pluginmanager.getplugins()
        plugins.append(self.modcol.obj)
        return pluginmanager.listattr(attrname=name, plugins=plugins)[-1]

    @property
    def testdir(self):
        return os.path.dirname(self.modcol.obj.__file__)

    @property
    def testname(self):
        return self.modcol.obj.__name__
        

_run = {}

def get_state(item, collect=False):
    modcol = item.getparent(py.test.collect.Module)
    try:
        return _run[modcol]
    except KeyError:
        pass
    _run[modcol] = state = RunState(modcol)
    if not collect:
        #print "ADD FINALIZER", os.getpid()
        #import traceback; traceback.print_stack()        
        modcol.config._setupstate.addfinalizer(colitem=modcol,
                                     finalizer=lambda: del_state(modcol))
    return state

def del_state(item):
    modcol = item.getparent(py.test.collect.Module)    
    state = _run.pop(modcol, None)
    if state:
        from oejskit.testing import cleanupBrowsers
        cleanupBrowsers(state)        

def pytest_collectstart(collector):
    if isinstance(collector, py.test.collect.Module):
        get_state(collector, collect=True)

def pytest_collectreport(rep):
    collector = rep.collector
    if isinstance(collector, py.test.collect.Module):
        del_state(collector)

def pytest_unconfigure(config):
    for colitem in _run.keys():
        del_state(colitem)

# ________________________________________________________________
# items

def give_browser(clsitem, attach=True):
    from oejskit.testing import giveBrowser
    return giveBrowser(get_state(clsitem), clsitem.obj, clsitem.browserKind,
                                                        attach=attach)

def detach_browser(clsitem):
    from oejskit.testing import detachBrowser
    detachBrowser(clsitem.obj)

def expand_browsers(config, kind):
    if kind is None:
        kind = 'any'

    # the command line takes precedence
    try:
        return jstests_cmdline_browser_specs[kind]
    except KeyError:
        pass

    try:
        specs = config.getvalue('jstests_browser_specs')
    except KeyError:
        pass
    else:
        try:
            return specs[kind]
        except KeyError:
            pass

    # assume kind identifies a single browser
    return [kind]

class ClassWithBrowserCollector(py.test.collect.Collector):
    def __init__(self, name, parent, browserKind):
        super(ClassWithBrowserCollector, self).__init__(name, parent)
        self.obj = getattr(self.parent.obj, name)
        self.browserKind = browserKind
       
    def collect(self):
        l = []
        kinds = expand_browsers(self.config, self.browserKind)
        for kind in kinds:
            name = "[=%s]" % kind
            classWithBrowser = ClassWithBrowser(name, self, self.obj, kind)
            l.append(classWithBrowser)
        return l

    def reportinfo(self):
        try:
            return self._fslineno, self.name
        except AttributeError:
            pass        
        fspath, lineno = py.code.getfslineno(self.obj)
        self._fslineno = fspath, lineno
        return fspath, lineno, self.name
    
class ClassWithBrowser(py.test.collect.Class):

    def __init__(self, name, parent, cls, browserKind):
        super(ClassWithBrowser, self).__init__(name, parent)
        self.obj = cls
        self.browserKind = browserKind

    def setup(self):
        browser, setupBag = give_browser(self, attach=True)
        super(ClassWithBrowser, self).setup()

    def teardown(self):
        super(ClassWithBrowser, self).teardown()
        detach_browser(self)

class JsTestSuite(py.test.collect.Collector):
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
        browser, setupBag = give_browser(clsitem, attach=False)
        url = obj._jstests_suite_url
        if not url.startswith('/'): # xxx wrong level
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

    def reportinfo(self):
        fspath, lineno = self.parent._getfslineno()
        return fspath, lineno, self.getmodpath()



