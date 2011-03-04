import os
import py
import pkg_resources

py_test_version = getattr(py.test, '__version__', None) or py.version
py_test_two = tuple(map(int, py_test_version.split('.')[:3])) >= (2, 0, 0)

pytest_plugins = "pytester"


def make_tests(testdir):
    p = testdir.makepyfile(test_js="""
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

    return p


def test_run(testdir, monkeypatch):
    monkeypatch.setenv('PYTHONPATH',
                       py.path.local(__file__).dirpath().dirpath())

    p = make_tests(testdir)

    #testdir.plugins.append("jstests")

    result = testdir.runpytest(p)

    assert result.ret == 0
    result.stdout.fnmatch_lines(["*test_js.py .."])


def test_collectonly(testdir, monkeypatch):
    monkeypatch.setenv('PYTHONPATH',
                       py.path.local(__file__).dirpath().dirpath())

    p = make_tests(testdir)

    #testdir.plugins.append("jstests")

    result = testdir.runpytest('--collectonly', p)

    assert result.ret == 0
    result.stdout.fnmatch_lines(["*test_one*", "*test_two*"])

# ________________________________________________________________


def check_clean(plugin):
    for state in plugin._run.values():
        assert not hasattr(state, '_jstests_browsers')
        assert not hasattr(state, '_jstests_browser_setups')


def test_run_cleanup(testdir, monkeypatch):
    if py_test_two:
        py.test.skip("not sensible for py.test 2.0")

    plugin = pkg_resources.load_entry_point('oejskit', 'pytest11',
                                            'pytest_jstests')
    p = make_tests(testdir)

    sanity = []
    def pytest_unconfigure(config):
        plugin = config.pluginmanager.getplugin("jstests")
        check_clean(plugin)
        sanity.append(None)

    testdir.plugins.extend([plugin,
                            {'pytest_unconfigure': pytest_unconfigure}])

    testdir.inline_run(p)

    assert sanity


def test_collectonly_cleanup(testdir, monkeypatch):
    if py_test_two:
        py.test.skip("not sensible for py.test 2.0")

    plugin = pkg_resources.load_entry_point('oejskit', 'pytest11',
                                            'pytest_jstests')
    p = make_tests(testdir)

    sanity = []
    def pytest_unconfigure(config):
        plugin = config.pluginmanager.getplugin("jstests")
        check_clean(plugin)
        sanity.append(None)

    testdir.plugins.extend([plugin,
                            {'pytest_unconfigure': pytest_unconfigure}])

    testdir.inline_run('--collectonly', p)

    assert sanity
