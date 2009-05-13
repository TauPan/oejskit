import oejskit.testing
from oejskit.testing import InBrowserSupport, inBrowser, JsFailed

class BrowserSupport(InBrowserSupport):
    from oejskit.wsgi import WSGIServerSide
    

BrowserSupport.install(globals())


class IntegrationStyleTests(BrowserTestClass):

    @inBrowser
    def test_serve_and_get(self):
        def ok(environ, start_response):
            start_response('200 OK', [('content-type', 'text/plain')])
            return ['ok\n']

        return self.gatherTests('/browser_testing/load/test/'
                                'test_integration_style.js', root=ok)    

class TestIntegrationStyleFirefo(IntegrationStyleTests):
    browserKind = 'firefox'

# ...
