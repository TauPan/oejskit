#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#
import py
        

class JstestsPlugin(object):

    jstests_setup = None

    def pytest_addoption(self, parser):
        group = parser.addgroup("jstests", "oejskit test suite options")
        group.addoption(
            "--jstests-server-side", action="store",
            dest="jstests_server_side",
            type="string",
            default="oejskit.wsgi.WSGIServerSide"
            )
        group.addoption(
            "--jstests-reuse-browser-windows", action="store_true",
            dest="jstests_reuse_browser_windows",
            )

    def pytest_pycollect_obj(self, collector, name, obj):
        if (collector.classnamefilter(name)) and \
            py.std.inspect.isclass(obj) and \
            (hasattr(obj, 'jstests_browser_kind') or \
             hasattr(obj, 'browserKind')):
            return ClassWithBrowser(name, parent=collector)
        return None

    def pytest_collectreport(self, rep):
        if isinstance(rep.colitem, py.test.collect.Module):
            from oejskit.testing import cleanupBrowsers
            cleanupBrowsers(rep.colitem.obj.__dict__)


class ClassWithBrowser(py.test.collect.Class):

    def setup(self):
        from oejskit.testing import attachBrowser        
        attachBrowser(self)
        super(py.test.collect.Class, self).setup()


