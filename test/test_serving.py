import cStringIO
from jskit.serving import Serve


class TestServe(object):

    def test_GET(self):
        calls = []

        class Get(Serve):

            def serve(self, path, data):
                calls.append((path, data))
                return 'text/plain', 'hello', False

        def start_response(status, headers):
            calls.append((status, headers))

        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/g'}
        res = Get()(environ, start_response)
        assert calls == [('/g', None), ('200 OK',
                                        [('content-type', 'text/plain'),
                                         ('cache-control', 'no-cache')])]
        assert res == ['hello']

        calls = []

        class Get2(Serve):

            def serve(self, path, data):
                calls.append((path, data))
                return ('text/plain', 'utf-8'), 'hello'
        
        environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/g2'}
        res = Get2()(environ, start_response)
        assert calls == [('/g2', None), ('200 OK',
                                         [('content-type',
                                           'text/plain; charset="utf-8"')])]
        assert res == ['hello']

    def test_POST(self):
        calls = []

        class Post(Serve):

            def serve(self, path, data):
                calls.append((path, data))
                return 'text/json', '42', False

        def start_response(status, headers):
            calls.append((status, headers))

        environ = {'REQUEST_METHOD': 'POST',
                   'wsgi.input': cStringIO.StringIO("post-data"),
                   'CONTENT_LENGTH': '9',
                   'PATH_INFO': '/a/b'}
        res = Post()(environ, start_response)
        assert calls == [('/a/b', 'post-data'), ('200 OK',
                                                 [('content-type', 'text/json'),
                                               ('cache-control', 'no-cache')])]
        assert res == ['42']

        
        
