import os

import mimetypes
from BaseHTTPServer import BaseHTTPRequestHandler
def status_string(code):
    return "%d %s" % (code, BaseHTTPRequestHandler.responses[code][0])
from wsgiref import headers

class Serve(object):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        if environ['REQUEST_METHOD'] == 'POST':
            length = environ.get('CONTENT_LENGTH')
            if length is None:
                data = ''
            else:
                data = environ['wsgi.input'].read(int(length))
        else:
            data = None

        resp = self.serve(path, data)
        if type(resp) is not tuple:
            resp = (resp,)
        return self.respond(start_response, *resp)

    def respond(self, start_response, data, mimetype='text/plain', cache=True):
        if type(data) is int:
            status = status_string(data)
            start_response(status, [])
            return [status+'\n']
        
        respHeaders = headers.Headers([])
        if type(mimetype) is tuple:
            mimetype, charset = mimetype
            respHeaders.add_header('content-type', mimetype,
                                   charset=charset)            
        else:
            respHeaders.add_header('content-type', mimetype)
        if not cache:
            respHeaders.add_header('cache-control', 'no-cache')

        start_response(status_string(200), respHeaders.items())
        return [data]

    def serve(self, path, data):
        raise NontImplementedError

class ServeFiles(Serve):

    def __init__(self, root, cache=True):
        self.root = root
        self.cache = cache

    def find(self, path):
        p = os.path.join(self.root, path)
        p = os.path.abspath(p)
        if not p.startswith(os.path.abspath(self.root)):
            return None
        if not os.path.isfile(p):
            return None
        if not os.access(p, os.R_OK):
            return None
        return p

    def serve(self, path, data):
        if data is not None:
            return 405
        if not path:
            return 404
        if path[0] != '/':
            return 404
        path = path[1:]
        if (not path or '..' in path or path[0] == '/' or
            path[-1] == '/'):
            return 404
        p = self.find(path)
        if p is None:
            return 404
        f = open(p, 'rb')
        try:
            data = f.read()
        finally:
            f.close()
        mimetype, _ = mimetypes.guess_type(p, True)
        return data, mimetype, self.cache
        

# ________________________________________________________________

class Application(Serve):

    def serve(self, path, data):
        return 'text/plain', 'PATH: %s' % path, False


import SocketServer
from wsgiref import simple_server, validate

class HTTPServer(SocketServer.ThreadingMixIn,
                 simple_server.WSGIServer):
    pass

if __name__ == '__main__':
    import sys
    app = validate.validator(Application())
    port = int(sys.argv[1])
    httpd = simple_server.make_server('', port, app, HTTPServer)
    print "serving at %d ..." % port
    httpd.serve_forever()
