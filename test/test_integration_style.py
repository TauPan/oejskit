import py

import oejskit.testing
from oejskit.testing import BrowserTestClass, inBrowser, JsFailed

class jstests_setup:
    from oejskit.wsgi import WSGIServerSide as ServerSide


class IntegrationStyleTests(BrowserTestClass):

    @inBrowser
    def test_serve_and_get(self):
        py.test.skip("WIP, broken style")
        def ok(environ, start_response):
            start_response('200 OK', [('content-type', 'text/plain')])
            return ['ok\n']

        return self.gatherTests('/browser_testing/load/test/'
                                'test_integration_style.js', root=ok)    

class TestIntegrationStyleFirefo(IntegrationStyleTests):
    jstests_browser_kind = 'firefox'

# ...
