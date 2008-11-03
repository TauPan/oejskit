from cStringIO import StringIO

from twisted.internet import defer
from twisted.web2 import (server, static, resource, http, channel, log,
                          http_headers, stream, responsecode)
from twisted_testing import support as reactor_supp

# good enough only for the js testing wsgi app which in particular is
# non-blocking
class NaiveWSGIRoot(resource.Resource):

    def __init__(self, app, stop):
        self.fallback = None
        self.app = app
        self.stop = stop
    
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
        env['jskit.stop_serving'] = self.stop

        result = self.app(env, start_response)
        
        return http.Response(code=code[0], headers=accumHeaders,
                             stream=''.join(result))


class TWeb2ServerSide(object):

    @staticmethod
    def cleanup():
        from twisted.internet import reactor
        reactor_supp.cleanup(reactor)

    def __init__(self, port, app):
        from twisted.internet import reactor
        self.root = NaiveWSGIRoot(app, self._stop)
        site = server.Site(self.root)
        self.port = reactor.listenTCP(port, channel.HTTPFactory(site))
        self.stopDeferred = None

    def _stop(self):
        self.stopDeferred.callback(None)

    def getPort(self):
        return self.port.getHost().port        

    def shutdown(self):
        self.port.stopListening()

    def serve_till_fulfilled(self, root, timeout):
        self.stopDeferred = defer.Deferred()
        try:
            self.root.fallback = root
            reactor_supp.consume(self.stopDeferred, timeout)
        finally:
            self.root.fallback = None
            self.stopDeferred = None
      
