import time
from wsgiref import simple_server
from SocketServer import ThreadingMixIn

class WSGIServer(ThreadingMixIn, simple_server.WSGIServer):
    pass

class WSGIServerSide(object):

    def __init__(self, port, app):
        self.app = app
        self.root = None
        self.done = False
        self.server = simple_server.make_server('', port, self._serve,
                                                server_class = WSGIServer)

    def _serve(self, environ, start_response):
        later = []
        def _stop():
            self.done = True
        environ['jskit.stop_serving'] = _stop
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
                del environ['jskit.stop_serving']
                return self.root(environ, start_response)
            else:
                start_response(*later)
        return stuff
            
    @staticmethod
    def cleanup():
        pass
    
    def shutdown(self):
        self.server.server_close()

    def getPort(self):
        return self.server.server_address[1]

    def serve_till_fulfilled(self, root, timeout):
        # self.server.socket.settimeout(timeout) meh
        self.root = root
        t0 = time.time()
        try:
            while time.time() - t0 <= timeout and not self.done:
                self.server.handle_request()
            if not self.done:
                raise RuntimeError("timeout")
        finally:
            self.root = None
            self.done = False
        
                                               
