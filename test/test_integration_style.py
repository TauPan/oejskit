import py

import oejskit.testing
from oejskit.testing import BrowserTestClass, jstests_suite

class jstests_setup:
    from oejskit.wsgi import WSGIServerSide as ServerSide

def setup_module(mod):
    mod.flag = False

def teardown_module(mod):
    assert mod.flag

class TestIntegrationStyle(BrowserTestClass):
    jstests_browser_kind = 'supported'

    def pytest_funcarg__ok_str(self, request):
        def set_flag():
            global flag
            flag = True
        request.addfinalizer(set_flag)
        return "ok\n"

    @jstests_suite('test_integration_style.js')
    def test_serve_and_get(self, ok_str):
        def ok(environ, start_response):
            start_response('200 OK', [('content-type', 'text/plain')])
            return [ok_str]

        return ok

