import py

import oejskit.testing
from oejskit.testing import BrowserTestClass, jstests_suite

class jstests_setup:
    from oejskit.wsgi import WSGIServerSide as ServerSide


def pytest_funcarg__ok_str(request):
    return "ok\n"

class IntegrationStyleTests(BrowserTestClass):

    @jstests_suite('test_integration_style.js')
    def test_serve_and_get(self, ok_str):
        def ok(environ, start_response):
            start_response('200 OK', [('content-type', 'text/plain')])
            return [ok_str]

        return ok

class TestIntegrationStyleFirefox(IntegrationStyleTests):
    jstests_browser_kind = 'firefox'

# ...
