import os
import py

pytest_plugins = ["pytester"]

@py.test.mark.xfail("failing because of generator tests shortcomings")
def test_run(testdir, monkeypatch):
    monkeypatch.setenv('PYTHONPATH',
                       py.path.local(__file__).dirpath().dirpath())
    
    p = testdir.makepyfile(test_js = """
    from oejskit.testing import BrowserTestClass, inBrowser

    class TestFirefox(BrowserTestClass):
         jstests_browser_kind = "firefox"

         @inBrowser
         def test_tests(self):
             return self.gatherTests("/browser_testing/load/test/test_tests.js")

    """)

    testdir.makefile('.js', test_tests="""
    Tests = {
        test_one: function() {
        },
        test_two: function() {
        }
    }
    """)
    
    testdir.plugins.append("jstests")
    testdir.prepare()

    result = testdir.runpytest(p)
    result.stdout.fnmatch_lines(["*test_js.py .."])

# xxx collectonly test
