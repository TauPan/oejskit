import os, tempfile, shutil, cStringIO
from wsgiref.util import shift_path_info
from oejskit.serving import Serve, ServeFiles, Dispatch


class TestServe(object):

    def test_GET(self):
        calls = []
        def start_response(status, headers):
            calls.append((status, headers))

        def get(env, data):
            calls.append((env['PATH_INFO'], data))
            return 'hello'

        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/g'}
        res = Serve(get)(environ, start_response)
        assert calls == [('/g', None), ('200 OK',
                                        [('content-type', 'text/plain')])]
        assert res == ['hello']
        
        calls = []

        class Get1(Serve):

            def serve(self, env, data):
                calls.append((env['PATH_INFO'], data))
                return 'hello', 'text/plain', False

        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/g1'}
        res = Get1()(environ, start_response)
        assert calls == [('/g1', None), ('200 OK',
                                        [('content-type', 'text/plain'),
                                         ('cache-control', 'no-cache')])]
        assert res == ['hello']

        calls = []

        class Get2(Serve):

            def serve(self, env, data):
                calls.append((env['PATH_INFO'], data))
                return 'hello', ('text/plain', 'utf-8')
        
        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/g2'}
        res = Get2()(environ, start_response)
        assert calls == [('/g2', None), ('200 OK',
                                         [('content-type',
                                           'text/plain; charset="utf-8"')])]
        assert res == ['hello']

    def test_POST(self):
        calls = []
        def start_response(status, headers):
            calls.append((status, headers))
            
        class Post(Serve):

            def serve(self, env, data):
                calls.append((env['PATH_INFO'], data))
                return '42', 'text/json', False


        environ = {'REQUEST_METHOD': 'POST',
                   'wsgi.input': cStringIO.StringIO("post-data"),
                   'CONTENT_LENGTH': '9',
                   'PATH_INFO': '/a/b'}
        res = Post()(environ, start_response)
        assert calls == [('/a/b', 'post-data'), ('200 OK',
                                                 [('content-type', 'text/json'),
                                               ('cache-control', 'no-cache')])]
        assert res == ['42']


    def test_not_200(self):
        calls = []

        class Get(Serve):

            def serve(self, env, data):
                return 405

        def start_response(status, headers):
            calls.append((status, headers))

        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/g'}
        res = Get()(environ, start_response)
        assert calls == [('405 Method Not Allowed', [])]
        assert res == ['405 Method Not Allowed\n']        


class TestServeFiles(object):

    @classmethod
    def setup_class(cls):
        cls.test_dir = tempfile.mkdtemp()
        p = lambda *segs:os.path.join(cls.test_dir, *segs)
        cls.root = p('staticFiles')
        os.mkdir(cls.root)
        a = open(p('staticFiles', 'a.txt'), 'w')
        a.write('a.\n')
        a.close()
        os.mkdir(p('staticFiles', 'sub'))
        b = open(p('staticFiles', 'sub', 'b.png'), 'w')
        b.write('PNG...')
        b.close()        

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.test_dir)


    def test_serve_file(self):
        calls = []
        def start_response(status, headers):
            calls.append((status, headers))
        
        static = ServeFiles(self.root, False)

        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/static/a.txt'}
        shift_path_info(environ)

        res = static(environ, start_response)
        assert calls == [('200 OK',
                          [('content-type', 'text/plain'),
                           ('cache-control', 'no-cache')])]
        assert ''.join(res).strip() == 'a.' # xxx

        calls = []
        static = ServeFiles(self.root)
        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/static/sub/b.png'}
        shift_path_info(environ)

        res = static(environ, start_response)
        assert calls == [('200 OK', [('content-type', 'image/png')])]
        assert res == ['PNG...']


    def test_fail(self):
        calls = []
        def start_response(status, headers):
            calls.append((status, headers))
            
        static = ServeFiles(self.root, False)

        def check(path, method='GET'):
            environ = {'REQUEST_METHOD': method, 'PATH_INFO': path,
                       }
            shift_path_info(environ)
            del calls[:]

            static(environ, start_response)
            return calls[0][0]

        res = check('/static/a.txt', method='POST')
        assert res == '405 Method Not Allowed'

        res = check('/static')
        assert res == '404 Not Found'

        res = check('/static/')
        assert res == '404 Not Found'

        res = check('/static/../x.sh')
        assert res == '404 Not Found'

        res = check('/static/x.txt')
        assert res == '404 Not Found'

        res = check('/static/sub')
        assert res == '404 Not Found'

        res = check('/static/sub/')
        assert res == '404 Not Found'

        res = check('/static/a.txt/')
        assert res == '404 Not Found'                        
            
class TestDispatch(object):

    def test_dispatch(self):
        calls = []
        def start_response(status, headers):
            calls.append((status, headers))

        def make_app(name):
            def app(environ, start_response):
                calls.append(environ['PATH_INFO'])
                return [name]
            return app

        a = make_app('a')
        ax = make_app('ax')
        b = make_app('b')
        root = make_app('root')

        d = Dispatch({'/a/': a,
                      '/a/x': ax,
                      '/b': b,
                      '/': root})

        def check(path):
            environ = {'PATH_INFO': path}
            res = d(environ, start_response)
            got = calls[:]
            del calls[:]
            return got, res

        outcome = check('/a/')
        assert outcome == (['/'], ['a'])

        outcome = check('/a/z')
        assert outcome == (['/z'], ['a'])

        outcome = check('/a/x')
        assert outcome == ([''], ['ax'])

        outcome = check('/a/x')
        assert outcome == ([''], ['ax'])

        outcome = check('/a/x/foo')
        assert outcome == ([('404 Not Found', [])], ['404 Not Found\n'])

        outcome = check('/b')
        assert outcome == ([''], ['b'])

        outcome = check('/z')
        assert outcome == (['/z'], ['root'])

        outcome = check('')
        assert outcome == ([('404 Not Found', [])], ['404 Not Found\n'])        

        # no root
        d = Dispatch({'/a/': a,
                      '/a/x': ax,
                      '/b': b })

        outcome = check('/z')
        assert outcome == ([('404 Not Found', [])], ['404 Not Found\n'])
        


            

        
