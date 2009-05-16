#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
"""
Python side infrastructure for running javascript tests in browsers
"""
import sys, os
import py

from oejskit.modular import jsDir
from oejskit.browser_ctl import ServeTesting, BrowserFactory, BrowserController
# convenience
from oejskit.browser_ctl import JsFailed


class SetupBag(object):
    _configs = [('staticDirs', dict),
                ('repoParents', dict),
                ('jsRepos', list),
                ('jsScripts', list),
                ('wsgiEndpoints', dict)]
    _update = {dict: dict.update, list: list.extend}

    def __init__(self, *sources):
        cfg = {}
        for prefix, typ in self._configs:
            cfg[prefix] = typ()
        for source in sources:
            if not source:
                continue
            for name in dir(source):
                for prefix, typ in self._configs:
                    if name.startswith(prefix):
                        SetupBag._update[typ](cfg[prefix],
                                              getattr(source, name))
        self.__dict__ = cfg

rtDir = os.path.join(os.path.dirname(__file__), 'testing_rt')

try:
    libDir = py.test.config.getvalue("jstests_weblib")
except KeyError:
    libDir = os.environ['WEBLIB'] # !


class BrowserTestClass(BrowserController):
    jstests_browser_kind = None


# ________________________________________________________________

def inBrowser(test):
    """
    py.test decorator, expects a test function returning the results of
    a browser.runTests invocation, produces a generative test
    reflecting back the browser-side tests one by one
    """
    overallName = test.__name__
            
    def runInBrowserTests(*args):
        names, runner = test(*args)
        assert names, ("%r no tests from the page: something is wrong" %
                        runner.url)
        for name in names:
                yield name, runner.runOneTest, name

    runInBrowserTests.__name__ = overallName
    runInBrowserTests.place_as = test
    return runInBrowserTests

# ________________________________________________________________

class DefaultJsTestsSetup:
    ServerSide = None
    # !
    staticDirs = { '/lib': libDir,
                   '/browser_testing/rt': rtDir,
                   '/oe-js': jsDir }                           
    jsRepos = ['/lib/mochikit', '/oe-js', '/browser_testing/rt']
    
def _get_jstests_setup(item):
    module = item._getparent(py.test.collect.Module).obj
    plugins = item.config.pluginmanager.getplugins()
    plugins.append(module)
    setup = item.config.pluginmanager.listattr(attrname='jstests_setup',
                                               plugins=plugins)[-1]
    return setup

def _get_serverSide(item):
    setup = _get_jstests_setup(item) or DefaultJsTestsSetup
    serverSide = setup.ServerSide
    if serverSide is None:
        serverSide = py.test.config.option.jstests_server_side
                        
    if isinstance(serverSide, str):
        p = serverSide.split('.')
        mod = __import__('.'.join(p[:-1]),
                         {}, {}, ['__doc__'])
        serverSide = getattr(mod, p[-1])

    return serverSide
   
def getBrowser(modCollector, browserKind):
    try:
        browsers = modCollector._jstests_browsers
    except AttributeError:
        browsers = modCollector._jstests_browsers = BrowserFactory()

    serverSide = _get_serverSide(modCollector)
    return browsers.get(browserKind, serverSide)

def cleanupBrowsers(modCollector):
    if hasattr(modCollector, '_jstests_browsers'):
        modCollector._jstests_browsers.shutdownAll()
        serverSide = _get_serverSide(modCollector)
        serverSide.cleanup()

def giveBrowser(item):
    try:
        return item._jstests_browser, item._jstests_setupBag
    except AttributeError:
        pass

    cls = item.obj
    
    modCollector = item._getparent(py.test.collect.Module)
    browserKind = getattr(cls, 'jstests_browser_kind')
                   
    # xxx wrong place
    if browserKind == 'iexplore' and sys.platform != 'win32':
        py.test.skip("iexplorer can be tested only on windows")
    if browserKind == 'safari' and sys.platform != 'darwin':
        py.test.skip("safari expects mac os x")                        

    browser = getBrowser(modCollector, browserKind)

    setup = _get_jstests_setup(item)

    mod_path = os.path.dirname(modCollector.obj.__file__)
    class modSetup:    
        staticDirsTest = {'/test/': mod_path}
        jsReposTest = ['/test']        

    if not hasattr(modCollector, '_jstests_app'):
        bootstrapSetupBag = SetupBag(DefaultJsTestsSetup, setup, modSetup)
        app = ServeTesting(bootstrapSetupBag, rtDir)
        modCollector._jstests_app = app

    setupBag = SetupBag(DefaultJsTestsSetup, setup, modSetup, cls)
    modName = modCollector.obj.__name__

    browser.prepare(modCollector._jstests_app, modName)

    item._jstests_browser = browser
    item._jstests_setupBag = setupBag

    return browser, setupBag

def jstests_suite(url):
    def decorate(func):
        func._jstests_suite_url = url
        return func
    return decorate
