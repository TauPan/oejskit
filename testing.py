#
# Copyright (C) Open End AB 2007-2008, All rights reserved
#
"""
Python side infrastructure for running javascript tests in browsers
"""
import sys, os, urllib
import subprocess
import simplejson

from jskit.serving import Serve, ServeFiles, Dispatch

PORT = 0
MANUAL = False
if MANUAL:
    PORT = 8116

# ________________________________________________________________

class ServeTesting(Dispatch):

    def __init__(self):
        self._cmd = {}
        self._results = {}
        
        self.rt = ServeFiles(os.path.join(os.path.dirname(__file__),
                                          'testing_rt'))
        self.extra = None
        map = {
            '/browser_testing/': self.home,
            '/browser_testing/cmd': Serve(self.cmd),
            '/browser_testing/result': Serve(self.result),
            '/browser_testing/rt/': self.rt,
            '/': self.varpart
            }
        Dispatch.__init__(self, map)

    def withSetup(self, setupBag, action):
        if setupBag:
            extraMap = {}
            for url, p in setupBag.staticDirs.items():
                if url[-1] != '/':
                    url += '/'
                extraMap[url] = ServeFiles(p)
            for url, app in setupBag.wsgiEndpoints.items():
                extraMap[url] = app
            self.extra = Dispatch(extraMap)
        self._cmd['CMD'] = action

    def reset(self):
        self.extra = None

    def getResult(self, key):
        return self._results.pop(key, None)
    
    def home(self, environ, start_response):
        environ['PATH_INFO'] = '/testing.html'
        return self.rt(environ, start_response)

    def cmd(self, env, data):
        cmd = self._cmd.pop('CMD', None)
        return simplejson.dumps(cmd), 'text/json', False

    def result(self, env, data):
        data = simplejson.loads(data)
        self._results[data['discrim']] = data['res']
        env['jskit.stop_serving']()
        return 'ok\n', 'text/plain', False

    def varpart(self, environ, start_response):
        if self.extra:
            return self.extra(environ, start_response)
        return self.notFound(start_response)
        

# ________________________________________________________________

class SetupBag(object):

    def __init__(self, *sources):
        staticDirs = {}
        jsRepos = {}
        jsScripts = []
        wsgiEndpoints = {}
        for source in sources:
            for name in dir(source):
                if name.startswith('staticDirs'):
                    staticDirs.update(getattr(source, name))
                elif name.startswith('jsRepos'):
                    jsRepos.update(getattr(source, name))
                elif name.startswith('jsScripts'):
                    jsScripts.extend(getattr(source, name))
                elif name.startswith('wsgiEndpoints'):
                    wsgiEndpoints.update(getattr(source, name))
                    
        self.staticDirs = staticDirs
        self.jsRepos = jsRepos
        self.jsScripts = jsScripts
        self.wsgiEndpoints = wsgiEndpoints

class Browser(object):
    """
    Control a launched browser and setup a server.  The
    launched browser will point to /browser_testing/ which serves
    testing_rt/testing.html
    """
    def __init__(self, name, ServerSide, bootstrapSetupBag):
        self.name = name
        self.process = None
        self.default_timeout = 30
        self.app = ServeTesting()
        self._startup_serving(ServerSide)
        self._startup_browser(bootstrapSetupBag)

    def makeurl(self, relative):
        baseurl = "http://localhost:%d/" % self.serverSide.getPort()
        return urllib.basejoin(baseurl, relative)
 
    def _startup_serving(self, ServerSide):
        self.serverSide = ServerSide(PORT, self.app)

    def _startup_browser(self, bootstrapSetupBag):
        url = self.makeurl('/browser_testing/')
        if MANUAL:
            print "open", url
            raw_input()
        elif sys.platform == 'win32':
            import win32api
            win32api.ShellExecute(0, None, self.name, url, None, 1)
        else:
            name = self.name
            if sys.platform == 'darwin':
                name = "open -a " + name.title()            
            print "%s %s" % (name, url)
            self.process = subprocess.Popen("%s %s" % (name, url), shell=True)
        r = self.send('InBrowserTesting.ping()', discrim='ping',
                      setupBag=bootstrapSetupBag)
        assert r == 'ping'

    def send(self, action, discrim=None, root=None, timeout=None,
             setupBag = None):
        """send javascript fragment for execution to the browser testing page"""
        if timeout is None:
            timeout = self.default_timeout
        if MANUAL:
            timeout = max(120, timeout)

        self.app.withSetup(setupBag, action)
        try:
            self.serverSide.serve_till_fulfilled(root, timeout)
        finally:
            self.app.reset()

        return self.app.getResult(discrim)
        
    def shutdown(self, killBrowser=False):
        if killBrowser and self.process:
            raise NotImplementedError
        self.serverSide.shutdown()

class BrowserFactory(object):

    def __init__(self):
        self._browsers = {}        

    def get(self, browserName, ServerSide, bootstrapSetupBag):
        _browsers = self._browsers
        try:
            return _browsers[browserName]
        except KeyError:
            browser = Browser(browserName, ServerSide, bootstrapSetupBag)
            _browsers[browserName] = browser
            return browser

    def shutdownAll(self):
        _browsers = self._browsers
        while _browsers:
            _, browser = _browsers.popitem()
            browser.shutdown()

# ________________________________________________________________

class Runner(object):

    def __init__(self, browser, root, url, timeout, setupBag):
        self.browser = browser
        self.root = root
        self.timeout = timeout
        self.url = url
        self.count = 0
        self.setupBag = setupBag

    def run(self, name):
        n = self.count
        self.count += 1
        b = self.browser
        outcome = b.send('InBrowserTesting.runOneTest(%r, %r, %d)' %
                         (self.url, str(name), n),
                         discrim="%s@%d" % (self.url, n),
                         root = self.root, setupBag=self.setupBag,
                         timeout=self.timeout)
        if not outcome['result']:
            py.test.fail('%s: %s' % (name, outcome['diag']))
        if outcome['leakedNames']:
            py.test.fail('%s leaked global names: %s' % (name,
                                                       outcome['leakedNames']))

class PageContext(object):

    def __init__(self, browser, root, url, index, timeout, setupBag):
        self.browser = browser
        self.root = root
        self.timeout = timeout
        self.url = url
        self.index = index
        self.count = 0
        self.setupBag = setupBag

    def eval(self, js):
        n = self.count
        self.count += 1
        b = self.browser
        outcome = b.send('InBrowserTesting.eval(%r, %s, %d)' %
                         (self.url, simplejson.dumps(js), n),
                         discrim="%s@%d" % (self.url, n),
                         root = self.root, setupBag=self.setupBag,
                         timeout=self.timeout)

        if outcome.get('error'):
            py.test.fail('[%s] %s: %s' % (self.url, js, outcome['error']))
        return outcome['result']
        

class BrowserController(object):
    browser = None
    setupBag = None
    default_root = None

    def open(self, url, root=None, timeout=None):
        """
        open url in a sub-iframe of the browser testing page.
        the iframe for a url is reused!
        """
        root = root or self.default_root
        res = self.browser.send('InBrowserTesting.open(%r)' % url,
                                root=root, discrim=url, setupBag=self.setupBag,
                                timeout=timeout)
        return PageContext(self, root, url, res['panel'], timeout,
                           self.setupBag)

    def gatherTests(self, url, root=None, timeout=None):
        root = root or self.default_root
        res = self.send('InBrowserTesting.collectTests(%r)' % url,
                        discrim="%s@collect" % url,
                        root = root, setupBag=self.setupBag,
                        timeout=timeout)
        return res, Runner(self, root, url, timeout, self.setupBag)

    def runTests(self, url, root=None, timeout=None):
        names, runner = self.gatherTests(url, root, timeout=timeout)
        for name in names:
            runner.run(name)

class InBrowserSupport(object):
    ServerSide = None

    def setup_module(self, mod):
        mod.browsers = BrowserFactory()

    def teardown_module(self, mod):
        mod.browsers.shutdownAll()
        del mod.browsers
        self.ServerSide.cleanup()

    @classmethod
    def install(supportCls, modDict):
        inst = supportCls()
        
        modDict['setup_module'] = inst.setup_module
        modDict['teardown_module'] = inst.teardown_module

        libDir = os.environ['WEBLIB'] # !

        class BrowserTestClass(BrowserController):
            browserKind = None

            staticDirs = { '/lib': libDir }
            
            @staticmethod
            def setup_class(cls):
                if cls.browserKind == 'iexplore' and sys.platform != 'win32':
                    py.test.skip("iexplorer can be tested only on windows")

                browsers = modDict['browsers']
                setupBag = SetupBag(supportCls, cls)
                cls.browser = browsers.get(cls.browserKind, inst.ServerSide,
                                           bootstrapSetupBag=setupBag)
                cls.setupBag = setupBag

        modDict['BrowserTestClass'] = BrowserTestClass
