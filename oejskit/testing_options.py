import py

def addoptions(server_side=False, reuse_browsers_windows=True):
    extra = []
    if server_side:
        extra.append(py.test.config.Option(
            "--js-tests-server-side", action="store",
            dest="js_tests_server_side",
            type="string",
            default="oejskit.wsgi.WSGIServerSide"
            ))

    if reuse_browsers_windows:
        extra.append(py.test.config.Option(
            "--js-tests-reuse-browser-windows", action="store_true",
            dest="js_tests_reuse_browser_windows",
            ))        
    if extra:        
        py.test.config.addoptions("oejskit test suite options", *extra)

