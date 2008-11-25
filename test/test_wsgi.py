from jskit import wsgi
#from wsgiref.validate import validator

def test_integration():
    calls = []
    def app(environ, start_response):
        path_info = environ['PATH_INFO']
        if 'stop' in path_info:
            start_response('200 OK', [('content-type', 'text/plain')])
            environ['jskit.stop_serving']()
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
        if 'other' in path_info: # xxx precision
            start_response('200 OK', [('content-type', 'text/plain')])
            return ['OTHER\n']            
        start_response('404 Not Found', [('content-type',
                                          'text/plain')])
        return ["???\n"]        

    serverSide = wsgi.WSGIServerSide(0, app)

    port = serverSide.getPort()
    
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
    
    serverSide.serve_till_fulfilled(other, 6*60)

    done.wait()
    assert results[0] == 'hello\n'
    assert results[1] == 'OTHER\n'

    
