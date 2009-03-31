#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
from cStringIO import StringIO

from twisted.internet import defer
from twisted.web2 import (server, static, resource, http, channel, log,
                          http_headers, stream, responsecode)
from twisted_testing import support as reactor_supp

# good enough only for the js testing wsgi app which in particular is
# non-blocking
class NaiveWSGIRoot(resource.Resource):

    def __init__(self, stop):
        self.stop = stop
        self.app = None
        self.fallback = None
    
    def locateChild(self, req, segments):
        if self.fallback:
            newres, newpath = self.fallback.locateChild(req, segments)
            if newres is not None:
                return newres, newpath

        return self, server.StopTraversal

    def renderHTTP(self, req, postData=None):
        if req.method == 'POST' and postData is None:
            postData = []
            d = stream.readStream(req.stream, postData.append)
            def gotPostData(_, req, postData):
                return self.renderHTTP(req, postData)
            d.addCallback(gotPostData, req, postData)
            return d

        if self.app is None:
            return http.Response(code=200, stream='null')  # xxx         
        
        code = [200]
        accumHeaders = http_headers.Headers()
        def start_response(status, headers):
            code[0] = int(status.split(' ')[0])
            for key, val in headers:
                accumHeaders.addRawHeader(key, val)
            # no write !

        env = {}
        env['REQUEST_METHOD'] = req.method
        env['PATH_INFO'] = '/'+'/'.join(req.postpath)
        if postData is not None:
            data = ''.join(postData)
            env['CONTENT_LENGTH'] = str(len(data))
            env['wsgi.input'] = StringIO(data)
        env['oejskit.stop_serving'] = self.stop

        result = self.app(env, start_response)
        
        return http.Response(code=code[0], headers=accumHeaders,
                             stream=''.join(result))


class TWeb2ServerSide(object):

    @staticmethod
    def cleanup():
        # xxx issues with reuse browser windows
        from twisted.internet import reactor
        reactor_supp.cleanup(reactor)

    def __init__(self, port):
        from twisted.internet import reactor
        self.root = NaiveWSGIRoot(self._stop)
        site = server.Site(self.root)
        self.port = reactor.listenTCP(port, channel.HTTPFactory(site))
        self.stopDeferred = None
        self.app = None

    def set_app(self, app):
        self.app = app

    def _stop(self):
        self.stopDeferred.callback(None)

    def get_port(self):
        return self.port.getHost().port        

    def shutdown(self):
        self.port.stopListening()

    def serve_till_fulfilled(self, root, timeout):
        self.stopDeferred = defer.Deferred()
        try:
            self.root.app = self.app
            self.root.fallback = root
            reactor_supp.consume(self.stopDeferred, timeout)
            # best effort to finish handling the last request
            from twisted.internet import reactor
            reactor.iterate(0)
        finally:
            self.root.app = None
            self.root.fallback = None
            self.stopDeferred = None
      
