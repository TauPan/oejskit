#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import py

class JstestsPlugin(object):

    def pytest_addoption(self, parser):
        group = parser.addgroup("jstests", "oejskit test suite options")
        group.addoption(
            "--js-tests-server-side", action="store",
            dest="js_tests_server_side",
            type="string",
            default="oejskit.wsgi.WSGIServerSide"
            )
        group.addoption(
            "--js-tests-reuse-browser-windows", action="store_true",
            dest="js_tests_reuse_browser_windows",
            )

