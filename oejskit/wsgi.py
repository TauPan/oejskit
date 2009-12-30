#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import time
import socket
from wsgiref import simple_server, handlers
from SocketServer import ThreadingMixIn

class WSGIRequestHandler(simple_server.WSGIRequestHandler):

    def log_request(self, code=None, size=None):
        pass

class WSGIServer(ThreadingMixIn, simple_server.WSGIServer):

    def get_request(self):
        (req_sock, addr) = simple_server.WSGIServer.get_request(self)
        req_sock.setblocking(1) # Mac OS X work-around
        return (req_sock, addr)

class WSGIServerSide(object):
    http_version = '1.1'

    def __init__(self, port):
        self.app = None
        self.root = None
        self.done = False
        self.server = simple_server.make_server('', port, self._serve,
                                            server_class = WSGIServer,
                                            handler_class = WSGIRequestHandler)
    def set_app(self, app):
        self.app = app

    def _serve(self, environ, start_response):
        later = []
        def _stop():
            self.done = True
        environ['oejskit.stop_serving'] = _stop
        def wrap_response(status, headers):
            status_code = int(status.split()[0])
            if status_code == 404:
                later[:] = [status, headers]
            else:
                start_response(status, headers)
            return # ! no write
        stuff = self.app(environ, wrap_response)
        if later:
            if self.root:
                del environ['oejskit.stop_serving']
                return self.root(environ, start_response)
            else:
                start_response(*later)
        return stuff
            
    @staticmethod
    def cleanup():
        pass
    
    def shutdown(self):
        self.server.server_close()

    def get_port(self):
        return self.server.server_port

    def serve_till_fulfilled(self, root, timeout):
        self.server.socket.settimeout(2)
        self.root = root
        # hack
        # IE seems not honor any no-caching headers unless we declare
        # to be serving HTTP/1.1
        orig_http_version = simple_server.ServerHandler.http_version
        simple_server.ServerHandler.http_version = self.http_version
        t0 = time.time()
        try:
            while time.time() - t0 <= timeout and not self.done:
                try:
                    self.server.handle_request()
                except socket.timeout:
                    pass
            if not self.done:
                raise socket.timeout
        finally:
            simple_server.ServerHandler.http_version = orig_http_version
            self.root = None
            self.done = False
        
                                               
