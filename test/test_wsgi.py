import py
import socket, time
from oejskit import wsgi
#from wsgiref.validate import validator

def test_timeout():
    def app(environ, start_response):
        start_response('200 OK', [('content-type', 'text/plain')])
        return ['stuff\n']        

    serverSide = wsgi.WSGIServerSide(0)
    port = serverSide.get_port()
    
    import threading, urllib2
    def get(rel):
        try:
            return urllib2.urlopen('http://localhost:%d/%s' % (port, rel)).read()
        except urllib2.HTTPError, e:
            return e.code, e.fp.read()

    results = []
    def requests():
        results.append(get('whatever'))
    threading.Thread(target=requests).start()

    serverSide.set_app(app)
    t0 = time.time()
    py.test.raises(socket.timeout, serverSide.serve_till_fulfilled, None, 3)
    t1 = time.time()

    assert results == ['stuff\n']
    assert 3.0 <= (t1-t0) <= 6.0

def test_integration():
    calls = []
    def app(environ, start_response):
        path_info = environ['PATH_INFO']
        if 'stop' in path_info:
            start_response('200 OK', [('content-type', 'text/plain')])
            environ['oejskit.stop_serving']()
            return ['ok\n']
        
        if not path_info.startswith('/x'):
            start_response('404 Not Found', [('content-type',
                                              'text/plain')])
            return ["WHAT?\n"]
        calls.append((environ['REQUEST_METHOD'], path_info))
        start_response('200 OK', [('content-type', 'text/plain')])
        return ['hello\n']


    def other(environ, start_response):
        path_info = environ['PATH_INFO']
        if path_info == '/other':
            start_response('200 OK', [('content-type', 'text/plain')])
            return ['OTHER\n']            
        start_response('404 Not Found', [('content-type',
                                          'text/plain')])
        return ["???\n"]        

    serverSide = wsgi.WSGIServerSide(0)

    port = serverSide.get_port()
    
    import threading, urllib2
    def get(rel):
        try:
            return urllib2.urlopen('http://localhost:%d/%s' % (port, rel)).read()
        except urllib2.HTTPError, e:
            return e.code, e.fp.read()

    done = threading.Event()
    results = []
    def requests():
        results.append(get('x'))
        results.append(get('other'))
        get('stop')
        done.set()    
    threading.Thread(target=requests).start()

    serverSide.set_app(app)
    serverSide.serve_till_fulfilled(other, 60)

    done.wait()
    assert results[0] == 'hello\n'
    assert results[1] == 'OTHER\n'

    
