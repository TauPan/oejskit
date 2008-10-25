from wsgiref import headers

class Serve(object):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        if environ['REQUEST_METHOD'] == 'POST':
            data = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
        else:
            data = None

        return self.respond(start_response, *self.serve(path, data))

    def respond(self, start_response, mimetype, data, cache=True):
        respHeaders = headers.Headers([])
        if type(mimetype) is tuple:
            mimetype, charset = mimetype
            respHeaders.add_header('content-type', mimetype,
                                   charset=charset)            
        else:
            respHeaders.add_header('content-type', mimetype)
        if not cache:
            respHeaders.add_header('cache-control', 'no-cache')

        start_response('200 OK', respHeaders.items())
        return [data]

    def serve(self, data):
        raise NontImplementedError


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
