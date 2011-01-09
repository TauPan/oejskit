import tempfile, shutil
import os, cStringIO, HTMLParser
import oejskit
import oejskit.modular
from oejskit.modular import JsResolver
from oejskit.htmlrewrite import naive_sanity_check_html

# use the well known MochiKit we include ourselves
weblibDir = os.path.join(os.path.dirname(oejskit.__file__), 'weblib')


class TestJsResolver(object):

    @classmethod
    def setup_class(cls):
        # xxx throw away once we have a real /js ?
        cls.test_dir = tempfile.mkdtemp()
        cls.jsDir = os.path.join(cls.test_dir, 'js')
        os.mkdir(cls.jsDir)
        os.mkdir(os.path.join(cls.test_dir, 'js', 'OpenEnd'))
        f = open(os.path.join(cls.test_dir, 'js', 'OpenEnd', 'Support.js'),
                 'w')
        f.write('// dummy\n')
        f.close()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.test_dir)

    def test__topSort(self):
        res = oejskit.modular._topSort({})
        assert res == []

        deps = {'X': ['A'], 'A': ['Y'], 'Y': []}
        res = oejskit.modular._topSort(deps)
        assert res == ['Y', 'A', 'X']

        deps = {'A': ['B', 'C'], 'C': ['B', 'D'], 'B': ['D'], 'D': []}
        res = oejskit.modular._topSort(deps)
        assert res == ['D', 'B', 'C', 'A']

    def test__findReposInFS(self):
        jsResolver = JsResolver()
        jsResolver.setRepoParents({
            '/lib': weblibDir,
            '/js': self.jsDir
            })

        repos = ['/lib/mochikit/', '/js', '']

        res = jsResolver._findReposInFS(repos)

        assert res == {
            self.jsDir: ['js'],
            os.path.join(weblibDir, 'mochikit'): ['lib', 'mochikit']
            }

        jsResolver.setRepoParents({
            '/lib/mochikit': os.path.join(weblibDir, 'mochikit'),
            '/js/': self.jsDir
            })

        repos = ['/lib/mochikit/', '/js', '']

        res = jsResolver._findReposInFS(repos)

        assert res == {
            self.jsDir: ['js'],
            os.path.join(weblibDir, 'mochikit'): ['lib', 'mochikit']
            }

    def test__find(self):
        jsResolver = JsResolver()
        fsRepos = {os.path.join(weblibDir, 'mochikit'):
                       ['lib', 'mochikit']}
        support = ['OpenEnd', 'Support.js']

        fp, path = jsResolver._find(support, fsRepos)
        assert fp is None
        assert path is None

        fsRepos = {os.path.join(weblibDir, 'mochikit'):
                       ['lib', 'mochikit'],
                   self.jsDir: ['js']
                   }
        fp, path = jsResolver._find(support, fsRepos)
        assert fp
        assert path == '/js/OpenEnd/Support.js'
        assert fp.exists()

    def test__simpleDeps(self):
        jsResolver = JsResolver()

        fsRepos = {os.path.join(weblibDir, 'mochikit'):
                       ['lib', 'mochikit']}

        acc = {}
        res = jsResolver._simpleDeps("Nonsense", fsRepos, acc)
        assert res is None
        assert acc == {}

        acc = {}
        res = jsResolver._simpleDeps("MochiKit.Style", fsRepos, acc)
        assert res == "/lib/mochikit/MochiKit/Style.js"

        assert acc == {
            '/lib/mochikit/MochiKit/DOM.js':
                ['/lib/mochikit/MochiKit/Base.js'],
            '/lib/mochikit/MochiKit/Style.js': [
            '/lib/mochikit/MochiKit/Base.js',
            '/lib/mochikit/MochiKit/DOM.js'],
            '/lib/mochikit/MochiKit/Base.js': []}

        res = jsResolver._simpleDeps("MochiKit.Signal", fsRepos, acc)
        assert res == "/lib/mochikit/MochiKit/Signal.js"

        assert acc == {
            '/lib/mochikit/MochiKit/DOM.js':
                ['/lib/mochikit/MochiKit/Base.js'],
            '/lib/mochikit/MochiKit/Style.js': [
            '/lib/mochikit/MochiKit/Base.js',
            '/lib/mochikit/MochiKit/DOM.js'],
            '/lib/mochikit/MochiKit/Base.js': [],
            '/lib/mochikit/MochiKit/Signal.js': [
            '/lib/mochikit/MochiKit/Base.js',
            '/lib/mochikit/MochiKit/DOM.js',
            '/lib/mochikit/MochiKit/Style.js']}

        acc = {}
        res = jsResolver._simpleDeps("/lib/mochikit/MochiKit/Style.js",
                                 fsRepos, acc)
        assert res == "/lib/mochikit/MochiKit/Style.js"
        assert acc == {
            '/lib/mochikit/MochiKit/DOM.js':
                ['/lib/mochikit/MochiKit/Base.js'],
            "/lib/mochikit/MochiKit/Style.js": [
            '/lib/mochikit/MochiKit/Base.js',
            '/lib/mochikit/MochiKit/DOM.js'],
            '/lib/mochikit/MochiKit/Base.js': []}

    def test__findDeps(self):
        jsResolver = JsResolver()

        fsRepos = {os.path.join(weblibDir, 'mochikit'):
                       ['lib', 'mochikit']}

        res = jsResolver._findDeps("MochiKit.Signal", fsRepos)

        assert res == ["/lib/mochikit/MochiKit/Base.js",
                       "/lib/mochikit/MochiKit/DOM.js",
                       "/lib/mochikit/MochiKit/Style.js",
                       "/lib/mochikit/MochiKit/Signal.js"]

        res = jsResolver._findDeps("/lib/mochikit/MochiKit/Style.js",
                              fsRepos)

        assert res == ["/lib/mochikit/MochiKit/Base.js",
                       "/lib/mochikit/MochiKit/DOM.js",
                       "/lib/mochikit/MochiKit/Style.js"]

    def test__parse_JSAN(self):
        data = """
        if (typeof(JSAN) != 'undefined') {
            JSAN.use("MochiKit.Base")
            JSAN.use("MochiKit.Iter")
            JSAN.use("MochiKit.Signal")
            JSAN.use("OpenEnd.Support", [])
            JSAN.use("OpenEnd.Object", [])
            JSAN.use("MochiKit.Base", ['bindMethods', 'update']);
            }
        """

        jsResolver = JsResolver()

        res = list(jsResolver._parse(data))
        assert res == ["MochiKit.Base", "MochiKit.Iter", "MochiKit.Signal",
                       "OpenEnd.Support", "OpenEnd.Object", "MochiKit.Base"]

    def test__parse_OpenEnd(self):
        data = """
        OpenEnd.use("MochiKit.Base")
        OpenEnd.use("MochiKit.Iter")
        OpenEnd.use("MochiKit.Signal")
        OpenEnd.use("OpenEnd.Support", [])
        OpenEnd.use("OpenEnd.Object", [])
        OpenEnd.use("MochiKit.Base", ['bindMethods', 'update']);

        OpenEnd.require("/foo/bar.js")

        """

        jsResolver = JsResolver()

        res = list(jsResolver._parse(data))
        assert res == ["MochiKit.Base", "MochiKit.Iter", "MochiKit.Signal",
                       "OpenEnd.Support", "OpenEnd.Object", "MochiKit.Base",
                       "/foo/bar.js"]

    def test__parse__deps(self):
        data = """
        MochiKit.Base._deps('Signal', ['Base', 'DOM', 'Style']);
        """

        jsResolver = JsResolver()

        res = list(jsResolver._parse(data))
        assert res == ["MochiKit.Base", "MochiKit.DOM", "MochiKit.Style"]

    def test__parseDepsData(self):
        calls = []

        class FakeFP(object):

            def exists(self):
                return True

            def open(self):
                calls.append('open')
                return self

            def getmtime(self):
                return self.mtime

            def read(self):
                return self.data

        fp = FakeFP()
        fp.mtime = 1
        fp.data = "DEPS"

        jsResolver = JsResolver()
        def _parse(data):
            yield "parsed"
            yield data
            yield "deps"

        jsResolver._parse = _parse

        res = jsResolver._parseDepsData("MODULE", fp)
        assert calls == ['open']
        assert res == sorted(['parsed', 'DEPS', 'deps'])
        calls = []

        res = jsResolver._parseDepsData("MODULE", fp)
        assert not calls
        assert res == sorted(['parsed', 'DEPS', 'deps'])

        fp.mtime = 2
        fp.data = "NEW DEPS"
        res = jsResolver._parseDepsData("MODULE", fp)
        assert calls == ['open']
        assert res == sorted(['parsed', 'NEW DEPS', 'deps'])
        calls = []

        res = jsResolver._parseDepsData("OTHER-MODULE", fp)
        assert calls == ['open']
        assert res == sorted(['parsed', 'NEW DEPS', 'deps'])
        calls = []

        res = jsResolver._parseDepsData("OTHER-MODULE", fp)
        assert not calls
        assert res == sorted(['parsed', 'NEW DEPS', 'deps'])
        calls = []

    def test_modified_check(self):
        calls = []

        class FakeFP(object):
            track = False

            def exists(self):
                return True

            def open(self):
                if self.track:
                    calls.append('open')
                return self

            def getmtime(self):
                return self.mtime

            def read(self):
                return self.data

        fakeFP = FakeFP()
        fakeFP.track = True
        otherFP = FakeFP()
        otherFP.mtime = 1
        otherFP.data = ''

        fsRepos = {'/path/to/mochikit':
                       ['lib', 'mochikit']}

        class TestRoot(JsResolver):

            def _find(self, segs, fsRepos):
                if segs == ['This', 'That.js']:
                    return fakeFP, '/place/This/That.js'
                if segs == ['MochiKit', 'Base.js']:
                    return otherFP, '/lib/mochikit/MochiKit/Base.js'

        testRoot = TestRoot()

        fakeFP.mtime = 1
        fakeFP.data = ""
        res = testRoot._findDeps("This.That", fsRepos)
        assert calls == ['open']
        assert res == ['/place/This/That.js']
        calls = []

        res = testRoot._findDeps("This.That", fsRepos)
        assert not calls
        assert res == ['/place/This/That.js']

        fakeFP.mtime = 2
        fakeFP.data = '  JSAN.use("MochiKit.Base")'
        res = testRoot._findDeps("This.That", fsRepos)
        assert calls == ['open']
        assert res == ['/lib/mochikit/MochiKit/Base.js',
                       '/place/This/That.js']

    def test_resolveHTML(self):
        html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html>
<head>
  <meta content="text/html; charset=utf-8" http-equiv="content-type" />
  <title>Open End Helpdesk</title>
  <link rel="stylesheet" type="text/css" href="/static/en/css/helpdesk.css" />
  <meta name="oe:jsRepos" content="/static" />
  <script type="text/javascript" src="/js/modular_rt.js"></script>
  <script type="text/javascript" src="/static/en/A.js"></script>
  <script type="text/javascript" src="/static/B.js"></script>
  <script type="text/javascript" src="/static/C.js"></script>
  <script type="text/javascript">
  function somefunc() {
  }
  </script>
</head>
<body>
</body>
</html>
"""
        jsResolver = JsResolver()

        def _findDeps(module, fsRepos):
            if module == '/static/en/A.js':
                return ['/static/en/A.js']
            elif module == '/static/B.js':
                return ['/js/Foo.js', '/js/Bar.js', '/static/B.js']
            elif module == '/static/C.js':
                return ['/js/Foo.js', '/js/Baz.js', '/static/C.js']
            else:
                return [module]

        jsResolver._fsRepos = lambda repos: None
        jsResolver._findDeps = _findDeps

        html2 = jsResolver.resolveHTML(html)
        naive_sanity_check_html(html2)

        srcs = []
        class Checker(HTMLParser.HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == 'script':
                    attrs = dict(attrs)
                    if 'src' in attrs:
                        srcs.append(attrs['src'])

        Checker().feed(html2)

        assert srcs == ['/js/modular_rt.js', '/static/en/A.js',
                        '/js/Foo.js', '/js/Bar.js', '/static/B.js',
                        '/js/Baz.js', '/static/C.js']

    def test_findDeps(self):
        jsResolver = JsResolver({'/lib': weblibDir},
                                defaultRepos=['/lib/mochikit'])

        res = jsResolver.findDeps("MochiKit.Signal")

        assert res == ["/lib/mochikit/MochiKit/Base.js",
                       "/lib/mochikit/MochiKit/DOM.js",
                       "/lib/mochikit/MochiKit/Style.js",
                       "/lib/mochikit/MochiKit/Signal.js"]

        res = jsResolver.findDeps("/lib/mochikit/MochiKit/Style.js")

        assert res == ["/lib/mochikit/MochiKit/Base.js",
                       "/lib/mochikit/MochiKit/DOM.js",
                       "/lib/mochikit/MochiKit/Style.js"]
