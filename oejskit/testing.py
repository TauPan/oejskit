#
# Copyright (C) Open End AB 2007-2008, All rights reserved
#
"""
Python side infrastructure for running javascript tests in browsers
"""
import sys, os, urllib
import subprocess
import py
import simplejson

from oejskit.serving import Serve, ServeFiles, Dispatch
from oejskit.modular import JsResolver, jsDir

PORT = 0
MANUAL = False
if MANUAL:
    PORT = 8116

rtDir = os.path.join(os.path.dirname(__file__), 'testing_rt')

# ________________________________________________________________
load_template = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html>
<head>
  <script type="text/javascript" src="/oe-js/modular_rt.js"></script>
  <script type="text/javascript" src="/browser_testing/rt/testing-new.js">
  </script>
  <script type="text/javascript" src="/browser_testing/rt/utils.js">
  </script>  

  <script type="text/javascript" src="%s">
  </script>  
</head>
<body>

<pre id="test">
</pre>

</body>
</html>
"""

class ServeTesting(Dispatch):

    def __init__(self, bootstrapSetupBag):
        self.bootstrapSetupBag = bootstrapSetupBag
        repoParents = {}
        repoParents.update(bootstrapSetupBag.staticDirs)
        repoParents.update(bootstrapSetupBag.repoParents)  
        self.jsResolver = JsResolver(repoParents)
        self._cmd = {}
        self._results = {}
        
        self.rt = ServeFiles(rtDir)
        self.extra = None
        map = {
            '/browser_testing/': self.home,
            '/browser_testing/cmd': Serve(self.cmd),
            '/browser_testing/result': Serve(self.result),
            '/browser_testing/rt/': self.rt,
            '/browser_testing/load/': Serve(self.load),
            '/': self.varpart
            }
        Dispatch.__init__(self, map)

    def withSetup(self, setupBag, action):
        setupBag = setupBag or self.bootstrapSetupBag
        
        extraMap = {}
        for url, p in setupBag.staticDirs.items():
            if url[-1] != '/':
                url += '/'
            extraMap[url] = ServeFiles(p)
        for url, app in setupBag.wsgiEndpoints.items():
            extraMap[url] = app
        self.extra = Dispatch(extraMap)

        self.repos = setupBag.jsRepos
        self._cmd['CMD'] = action

    def reset(self):
        self.extra = None
        self.repos = None

    def getResult(self, key):
        return self._results.pop(key, None)
    
    def home(self, environ, start_response):
        environ['PATH_INFO'] = '/testing.html'
        return self.rt(environ, start_response)

    def cmd(self, env, data):
        cmd = self._cmd.pop('CMD', None)
        return simplejson.dumps(cmd), 'text/json', False

    def result(self, env, data):
        if data is None:
            return '', 'text/plain', False # not clear why we get a GET
        data = simplejson.loads(data)
        self._results[data['discrim']] = data['res']
        env['oejskit.stop_serving']()
        return 'ok\n', 'text/plain', False

    def varpart(self, environ, start_response):
        if self.extra:
            return self.extra(environ, start_response)
        return self.notFound(start_response)

    def load(self, env, path):
        page = load_template % env['PATH_INFO']
        page = self.jsResolver.resolveHTML(page, repos=self.repos)
        return page, 'text/html'


# ________________________________________________________________

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


class Browser(object):
    """
    Control a launched browser and setup a server.  The
    launched browser will point to /browser_testing/ which serves
    testing_rt/testing.html
    """
    def __init__(self, name, ServerSide):
        self.name = name
        self.process = None
        self.default_timeout = 30
        self.app = None
        self.serverSide = ServerSide(PORT)
        self._startup_browser()

    def makeurl(self, relative):
        baseurl = "http://localhost:%d/" % self.serverSide.get_port()
        return urllib.basejoin(baseurl, relative)
 
    def _startup_browser(self):
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

    def prepare(self, app, name="suite"):
        self.app = app
        self.serverSide.set_app(app)
        r = self.send('InBrowserTesting.prepare(%r)' % name,
                      discrim='prepared:%s' % name)
        assert r == 'prepared'        

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

reuse_windows = False # XXX from conftest or option !

class BrowserFactory(object):
    _inst = None

    def __new__(cls):
        if reuse_windows and cls._inst:
            return cls._inst
        obj = object.__new__(BrowserFactory)
        obj._browsers = {}
        if reuse_windows:
            cls._inst = obj
        return obj

    def get(self, browserName, ServerSide):
        _browsers = self._browsers
        key = (browserName, ServerSide)
        try:
            return _browsers[key]
        except KeyError:
            browser = Browser(browserName, ServerSide)
            _browsers[key] = browser
            return browser

    def shutdownAll(self):
        if not reuse_windows:
            _browsers = self._browsers
            while _browsers:
                _, browser = _browsers.popitem()
                browser.shutdown()

# ________________________________________________________________

class PageContext(object):

    def __init__(self, browserController, root, url, timeout, index=None):
        self.browserController = browserController
        self.root = root
        self.timeout = timeout
        self.url = url
        self.count = 0
        self.index = index

    def _execute(self, method, argument):
        n = self.count
        self.count += 1
        browser = self.browserController.browser
        setupBag = self.browserController.setupBag
        outcome = browser.send('InBrowserTesting.%s(%r, %s, %d)' %
                         (method, self.url, simplejson.dumps(argument), n),
                         discrim="%s@%d" % (self.url, n),
                         root = self.root, setupBag=setupBag,
                         timeout=self.timeout)
        return outcome
        
    def eval(self, js):
        outcome = self._execute('eval', js)
        if outcome.get('error'):
            py.test.fail('[%s] %s: %s' % (self.url, js, outcome['error']))
        return outcome['result']

    def runOneTest(self, name):
        outcome = self._execute('runOneTest', name)
        if not outcome['result']:
            py.test.fail('%s: %s' % (name, outcome['diag']))
        if outcome['leakedNames']:
            py.test.fail('%s leaked global names: %s' % (name,
                                                       outcome['leakedNames']))
        

class BrowserController(object):
    browser = None
    setupBag = None
    default_root = None

    def send(self, action, discrim=None, root=None, timeout=None):
        root = root or self.default_root        
        return self.browser.send(action, discrim=discrim, root=root,
                                 setupBag=self.setupBag, timeout=timeout)

    def open(self, url, root=None, timeout=None):
        """
        open url in a sub-iframe of the browser testing page.
        the iframe for a url is reused!
        """
        root = root or self.default_root
        res = self.send('InBrowserTesting.open(%r)' % url,
                        root=root, discrim=url, timeout=timeout)
        return PageContext(self, root, url, timeout, res['panel'])

    def gatherTests(self, url, root=None, timeout=None):
        root = root or self.default_root
        res = self.send('InBrowserTesting.collectTests(%r)' % url,
                        discrim="%s@collect" % url, root = root,
                        timeout=timeout)
        return res, PageContext(self, root, url, timeout)

    def runTests(self, url, root=None, timeout=None):
        names, runner = self.gatherTests(url, root, timeout=timeout)
        for name in names:
            runner.runOneTest(name)

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
        inst.staticDirsTest = {'/test/': os.path.dirname(modDict['__file__'])}
        inst.jsReposTest = ['/test']
        inst.__dict__.update(configs)
        
        modDict['setup_module'] = inst.setup_module
        modDict['teardown_module'] = inst.teardown_module

        bootstrapSetupBag = SetupBag(inst)
        app = ServeTesting(bootstrapSetupBag)

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
                        serverSide = py.test.config.getvalue("js_tests_server_side")
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
