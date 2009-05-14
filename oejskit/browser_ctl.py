#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
"""
Controlling browsers for javascript testing
"""
import sys, urllib
import subprocess
import py
import simplejson

from oejskit.serving import Serve, ServeFiles, Dispatch
from oejskit.modular import JsResolver

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

    def __init__(self, bootstrapSetupBag, rtDir):
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

PORT = 0
MANUAL = False
if MANUAL:
    PORT = 8116

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

try:
    reuse_windows = py.test.config.getvalue("js_tests_reuse_browser_windows")
except KeyError:
    reuse_windows = False

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

class JsFailed(Exception):

    def __init__(self, name, msg):
        self.name = name
        self.msg = msg

    def __str__(self):
        return "%s: %s" % (self.name, self.msg)


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
            raise JsFailed('[%s] %s' % (self.url, js), outcome['error'])
        return outcome['result']

    def runOneTest(self, name):
        outcome = self._execute('runOneTest', name)
        if not outcome['result']:
            raise JsFailed(name, outcome['diag'])
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
