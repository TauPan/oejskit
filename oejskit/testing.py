#
# Copyright (C) Open End AB 2007-2011, All rights reserved
# See LICENSE.txt
#
"""
Python side infrastructure for running javascript tests in browsers
"""
import sys, os

from oejskit.modular import jsDir
from oejskit.browser_ctl import ServeTesting, BrowserFactory, BrowserController
# convenience
from oejskit.browser_ctl import JsFailed


def _getglobal(state, name, default):
    try:
        return state.getglobal(name)
    except AttributeError:
        return default


def _getscoped(state, name):
    try:
        return getattr(state, name)
    except AttributeError:
        pass
    try:
        return state.getscoped(name)
    except AttributeError:
        return None


def _ensure(obj, name, default):
    try:
        return getattr(obj, name)
    except AttributeError:
        setattr(obj, name, default)
        return default


class SetupBag(object):
    name = 'other'

    _opts = {'MochiKit__export__': False}
    _configs = [('staticDirs', dict),
                ('repoParents', dict),
                ('jsRepos', list),
                ('jsScripts', list),
                ('wsgiEndpoints', dict)]
    _update = {dict: dict.update, list: list.extend}

    def __init__(self, *sources):
        cfg = {}
        for name, dfl in self._opts.iteritems():
            cfg[name] = dfl
        for prefix, typ in self._configs:
            cfg[prefix] = typ()
        for source in sources:
            if not source:
                continue
            for name in dir(source):
                if name in self._opts:
                    cfg[name] = getattr(source, name)
                    continue
                for prefix, typ in self._configs:
                    if name.startswith(prefix):
                        SetupBag._update[typ](cfg[prefix],
                                              getattr(source, name))
        self.__dict__ = cfg


rtDir = os.path.join(os.path.dirname(__file__), 'testing_rt')


def defaultJsTestsSetup(state):
    libDir = os.environ.get('WEBLIB')
    if libDir is None:
        libDir = os.path.join(os.path.dirname(__file__), 'weblib')

    libDir = _getglobal(state, 'jstests_weblib', libDir)

    class DefaultJsTestsSetup:
        ServerSide = None
        # !
        staticDirs = {'/lib': libDir,
                       '/browser_testing/rt': rtDir,
                       '/oe-js': jsDir}
        jsRepos = ['/lib/mochikit', '/oe-js', '/browser_testing/rt']

    return DefaultJsTestsSetup, libDir

# ________________________________________________________________


def _get_serverSide(state):
    setup = _getscoped(state, "jstests_setup")
    if not setup:
        setup, _ = defaultJsTestsSetup(state)
    serverSide = getattr(setup, 'ServerSide', None)
    if serverSide is None:
        serverSide = _getglobal(state, "jstests_server_side",
                                "oejskit.wsgi.WSGIServerSide")

    if isinstance(serverSide, str):
        p = serverSide.split('.')
        mod = __import__('.'.join(p[:-1]),
                         {}, {}, ['__doc__'])
        serverSide = getattr(mod, p[-1])

    return serverSide


def getBrowser(state, browserKind):
    browsers = _ensure(state, '_jstests_browsers', None)
    if browsers is None:
        reuse_windows = _getglobal(state,
                                   "jstests_reuse_browser_windows", True)
        browsers = BrowserFactory(reuse_windows)
        state._jstests_browsers = browsers

    serverSide = _get_serverSide(state)
    return browsers.get(browserKind, serverSide)


def cleanupBrowsers(state):
    reuse_windows = _getglobal(state,
                               "jstests_reuse_browser_windows", True)
    if reuse_windows:
        return

    if hasattr(state, '_jstests_browsers'):
        #print 'CLEANUP', os.getpid()
        #import traceback; traceback.print_stack()
        state._jstests_browsers.shutdownAll()
        serverSide = _get_serverSide(state)
        serverSide.cleanup()
        del state._jstests_browsers
        try:
            del state._jstests_browser_setups
        except AttributeError:
            pass


def checkBrowser(browserKind):
    from oejskit.browser import check_browser
    return check_browser(browserKind)


def giveBrowser(state, cls, browserKind, attach=True):
    browser_setups = _ensure(state, '_jstests_browser_setups', {})
    try:
        browser, setupBag = browser_setups[(cls, browserKind)]
    except KeyError:
        browser = getBrowser(state, browserKind)

        setup = _getscoped(state, 'jstests_setup')

        class modSetup:
            staticDirsTest = {'/test/': state.testdir}
            jsReposTest = ['/test']

        defaultSetup, libDir = defaultJsTestsSetup(state)

        # keep the server side state of browser cmds/responses
        # isolated with one app per browser
        if not browser.app:
            app = ServeTesting(rtDir, libDir)
            browser.set_app(app)

        setupBag = SetupBag(defaultSetup, setup, modSetup, cls)
        setupBag.name = state.testname

        browser.prepare(setupBag)

        browser_setups[(cls, browserKind)] = browser, setupBag

    if attach:
        cls.browser = browser
        cls.setupBag = setupBag

    return browser, setupBag


def detachBrowser(cls):
    del cls.setupBag
    del cls.browser

# ________________________________________________________________


def jstests_suite(url):
    def decorate(func):
        func._jstests_suite_url = url
        return func
    return decorate


class BrowserTestClass(BrowserController):
    jstests_browser_kind = None
