import py

option = py.test.config.addoptions("oejskit test suite options",
            py.test.config.Option("--js-tests-server-side", action="store",
                                  dest="js_tests_server_side",
                                  type="string",
                                  default="oejskit.wsgi.WSGIServerSide"
                                  ))



