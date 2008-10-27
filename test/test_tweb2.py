from twisted.internet import defer
from twisted.web2 import (server, static, resource, http, channel, log,
                          http_headers, stream, responsecode)
from twisted_testing import support as reactor_supp

from jskit import tweb2
#from wsgiref.validate import validator

def teardown_module(mod):
    from twisted.internet import reactor
    reactor_supp.cleanup(reactor)

def test_min_sanity():
    calls = []
    def app(environ, start_response):
        calls.append((environ['REQUEST_METHOD'], environ['PATH_INFO']))
        start_response('200 OK', [('content-type', 'text/plain')])
        environ['jskit.stop_serving']()
        return ['hello']

    def stop():
        calls.append('Stop')

    res = tweb2.NaiveWSGIRoot(app, stop)

    req = server.Request(None, "GET", "/x/y", "HTTP/1.1",
                         0, http_headers.Headers())
    req._parseURL() # !

    resp = res.renderHTTP(req)

    assert calls == [('GET', '/x/y'), 'Stop']

    assert resp.code == 200
    data =  str(resp.stream.read()) # one-shot, depends on internals
    assert data == 'hello'
    rawheaders = sorted(resp.headers.getAllRawHeaders())
    assert rawheaders == [('Content-Type', ['text/plain'])]

def test_POST():
    calls = []
    def app(environ, start_response):
        calls.append(environ['CONTENT_LENGTH'])
        start_response('200 OK', [('content-type', 'text/plain')])
        data = environ['wsgi.input'].read()
        return ['+%s+' % data]
    
    res = tweb2.NaiveWSGIRoot(app, None)

    req = server.Request(None, "POST", "/x/y", "HTTP/1.1",
                         0, http_headers.Headers())
    req._parseURL() # !
    class FakeStream(object):
        deferredData = None
        
        def read(self):
            if self.deferredData is None:
                self.deferredData = defer.Deferred()
                return self.deferredData
            return None

    req.stream = FakeStream()

    dresp = res.renderHTTP(req)
    assert isinstance(dresp, defer.Deferred)

    req.stream.deferredData.callback('stuff')
    resp = reactor_supp.consume(dresp, 10)

    assert resp.code == 200
    data =  str(resp.stream.read()) # one-shot, depends on internals
    assert data == '+stuff+'
    assert calls == ['5']
