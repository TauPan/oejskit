#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import os

import mimetypes
from BaseHTTPServer import BaseHTTPRequestHandler
def status_string(code):
    return "%d %s" % (code, BaseHTTPRequestHandler.responses[code][0])
from wsgiref import headers
from wsgiref.util import shift_path_info

class Serve(object):

    def __init__(self, servefunc=None):
        if servefunc:
            self.serve = servefunc

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'POST':
            length = environ.get('CONTENT_LENGTH')
            if length is None:
                data = ''
            else:
                data = environ['wsgi.input'].read(int(length))
        else:
            data = None

        resp = self.serve(environ, data)
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

class Dispatch(object):

    def __init__(self, appmap):
        self.appmap = sorted(appmap.items(), reverse=True)

    def notFound(self, start_response):
        status = status_string(404)
        start_response(status, [])
        return [status+'\n']        

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        for prefix, app in self.appmap:
            if path.startswith(prefix):
                slashes = prefix.count('/')
                if prefix[-1] != '/':
                    if path != prefix:
                        break
                    slashes += 1
                for i in range(slashes-1):
                    shift_path_info(environ)
                return app(environ, start_response)
        # no match
        return self.notFound(start_response)
        

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

    def serve(self, env, data):
        if data is not None:
            return 405
        path = env['PATH_INFO']
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
