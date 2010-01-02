#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
"""
Controlling browsers for javascript testing
"""
import sys, urllib
import subprocess
try:
    import json
except ImportError:
    import simplejson as json

from oejskit.serving import Serve, ServeFiles, Dispatch
from oejskit.modular import JsResolver
from oejskit.browser import start_browser

script_template = """
  <script type="text/javascript" src="%s">
  </script>  
"""

load_template = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html>
<head>
  <script type="text/javascript" src="/oe-js/modular_rt.js"></script>
  <script type="text/javascript" src="/browser_testing/rt/testing-new.js">
  </script>
  <script type="text/javascript" src="/browser_testing/rt/utils.js">
  </script>  

  %s
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

    def __init__(self, bootstrapSetupBag, rtDir, libDir):
        self.bootstrapSetupBag = bootstrapSetupBag
        repoParents = {}
        repoParents.update(bootstrapSetupBag.staticDirs)
        repoParents.update(bootstrapSetupBag.repoParents)  
        self.jsResolver = JsResolver(repoParents)
        self._cmd = {}
        self._results = {}
        
        self.rt = ServeFiles(rtDir)
        self.lib = ServeFiles(libDir)
        self.extra = None
        self.jsScripts = None
        map = {
            '/browser_testing/': self.home,
            '/browser_testing/cmd': Serve(self.cmd),
            '/browser_testing/result': Serve(self.result),
            '/browser_testing/rt/': self.rt,
            '/browser_testing/lib/': self.lib,
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
        self.jsScripts = setupBag.jsScripts
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
        return json.dumps(cmd), 'text/json', False

    def result(self, env, data):
        if data is None:
            return '', 'text/plain', False # not clear why we get a GET
        data = json.loads(data)
        self._results[data['discrim']] = data['res']
        env['oejskit.stop_serving']()
        return 'ok\n', 'text/plain', False

    def varpart(self, environ, start_response):
        if self.extra:
            return self.extra(environ, start_response)
        return self.notFound(start_response)

    def load(self, env, path):
        scripts = []
        for url in self.jsScripts:
            scripts.append(script_template % url)
        scripts = ''.join(scripts)
        page = load_template % (scripts, env['PATH_INFO'])
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
        self.default_timeout = 60
        self.app = None
        self.serverSide = ServerSide(PORT)
        self._startup_browser()

    def makeurl(self, relative):
        baseurl = "http://localhost:%d/" % self.serverSide.get_port()
        return urllib.basejoin(baseurl, relative)
 
    def _startup_browser(self):
        url = self.makeurl('/browser_testing/')
        start_browser(self.name, url, manual=MANUAL)

    def prepare(self, app, name="suite"):
        self.app = app
        self.serverSide.set_app(app)
        r = self.send('InBrowserTesting.prepare(%r)' % name,
                      discrim='prepared:%s' % name, timeout=20)
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

    def _gatherTests(self, url, setupBag):
        if not url.startswith('/'):
            url = "/browser_testing/load/test/%s" % url        
        res = self.send('InBrowserTesting.collectTests(%r)' % url,
                        discrim="%s@collect" % url)

        assert res, ("%r no tests from the page: something is wrong" % url)

        return res, PageContext(self, setupBag,  None, url)
        
    def shutdown(self):
        self.send('BYE', discrim='BYE')        
        self.serverSide.shutdown()

class BrowserFactory(object):
    _inst = None

    def __new__(cls, reuse_windows):
        if reuse_windows and cls._inst:
            return cls._inst
        obj = object.__new__(BrowserFactory)
        obj._browsers = {}
        obj.reuse_windows = reuse_windows
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
        if not self.reuse_windows:
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

class _BrowserController(object):
    browser = None
    setupBag = None

    def send(self, action, discrim=None, root=None, timeout=None):
        return self.browser.send(action, discrim=discrim, root=root,
                                 setupBag=self.setupBag, timeout=timeout)

class PageContext(_BrowserController):

    def __init__(self, browser, setupBag, root, label, timeout=None, index=None):
        self.browser = browser
        self.setupBag = setupBag
        self.root = root
        self.timeout = timeout
        self.label = label
        self.count = 0
        self.index = index

    def _execute(self, method, argument, root, timeout):
        n = self.count
        self.count += 1
        outcome = self.send('InBrowserTesting.%s(%r, %s, %d)' %
                         (method, self.label, json.dumps(argument), n),
                         discrim="%s@%d" % (self.label, n),
                         root=root, timeout=timeout)
        return outcome
        
    def eval(self, js, variant='eval'):
        outcome = self._execute(variant, js, self.root, self.timeout)
        if outcome.get('error'):
            raise JsFailed('[%s] %s' % (self.label, js), outcome['error'])
        return outcome['result']

    def travel(self, js):
        return self.eval(js, variant='travel')
    

    def _runTest(self, name, root, timeout):
        outcome = self._execute('runOneTest', name, root, timeout)
        if not outcome['result']:
            raise JsFailed(name, outcome['diag'])
        if outcome['leakedNames']:
            raise RuntimeError('%s leaked global names: %s' % (name,
                                                       outcome['leakedNames']))
        

class BrowserController(_BrowserController):

    def open(self, url, root=None, timeout=None, take=None):
        """
        open url in a sub-iframe of the browser testing page.
        the iframe for a url is reused!
        """
        label = url
        if take:
            label = "%s >%s<" % (url, take)
        
        res = self.send('InBrowserTesting.open(%r, %r)' % (url, label),
                        root=root, discrim=label, timeout=timeout)
        return PageContext(self.browser, self.setupBag, root, label,
                                                        timeout, res['panel'])

    def runTests(self, url, root=None, timeout=None):
        names, runner = self.browser._gatherTests(url, self.setupBag)
        for name in names:
            runner._runTest(name, root, timeout)
