import os
import py

pytest_plugins = ["pytester"]

def test_run(testdir, monkeypatch):
    monkeypatch.setenv('PYTHONPATH',
                       py.path.local(__file__).dirpath().dirpath())
    
    p = testdir.makepyfile(test_js = """
    from oejskit.testing import BrowserTestClass, jstests_suite

    class TestFirefox(BrowserTestClass):
         jstests_browser_kind = "firefox"

         @jstests_suite('test_tests.js')
         def test_tests(self):
             pass

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
# xxx test failure
