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
            for name in dir(source):
                for prefix, typ in self._configs:
                    if name.startswith(prefix):
                        SetupBag._update[typ](cfg[prefix],
                                              getattr(source, name))
        self.__dict__ = cfg

rtDir = os.path.join(os.path.dirname(__file__), 'testing_rt')

try:
    libDir = py.test.config.getvalue("js_tests_weblib")
except KeyError:
    libDir = os.environ['WEBLIB'] # !

class InBrowserSupport(object):
    ServerSide = None
    # !
    staticDirs = { '/lib': libDir,
                   '/browser_testing/rt': rtDir,
                   '/oe-js': jsDir }                           
    jsRepos = ['/lib/mochikit', '/oe-js', '/browser_testing/rt']

    def setup_module(self, mod):
        mod.browsers = BrowserFactory()

    def teardown_module(self, mod):
        mod.browsers.shutdownAll()
        del mod.browsers
        self.ServerSide.cleanup()

    @classmethod
    def install(supportCls, modDict, configs={}):
        inst = supportCls()
        mod_path = os.path.dirname(modDict['__file__'])
        
        inst.staticDirsTest = {'/test/': mod_path}
        inst.jsReposTest = ['/test']
        inst.__dict__.update(configs)
        
        modDict['setup_module'] = inst.setup_module
        modDict['teardown_module'] = inst.teardown_module

        bootstrapSetupBag = SetupBag(inst)
        app = ServeTesting(bootstrapSetupBag, rtDir)

        modName = modDict["__name__"]

        class BrowserTestClass(BrowserController):
            browserKind = None
            
            @staticmethod
            def setup_class(cls):
                if cls.browserKind == 'iexplore' and sys.platform != 'win32':
                    py.test.skip("iexplorer can be tested only on windows")
                if cls.browserKind == 'safari' and sys.platform != 'darwin':
                    py.test.skip("safari expects mac os x")                    

                browsers = modDict['browsers']
                setupBag = SetupBag(inst, cls)

                serverSide = inst.ServerSide
                if serverSide is None:
                    try:
                        serverSide = py.test.config.getvalue(
                            "js_tests_server_side", py.path.local(mod_path))
                    except KeyError:
                        serverSide = "oejskit.wsgi.WSGIServerSide" 
                        
                    if isinstance(serverSide, str):
                        p = serverSide.split('.')
                        mod = __import__('.'.join(p[:-1]),
                                         {}, {}, ['__doc__'])
                        serverSide = getattr(mod, p[-1])

                    inst.ServerSide = serverSide
                    
                cls.browser = browsers.get(cls.browserKind, serverSide)
                cls.browser.prepare(app, modName)
                
                cls.setupBag = setupBag

        modDict['BrowserTestClass'] = BrowserTestClass

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
