import os
import py
import pkg_resources

pytest_plugins = "pytester"

def make_tests(testdir):
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


def test_looponfail_cleanup(testdir, monkeypatch):
    # xxx too much white boxy
    plugin = pkg_resources.load_entry_point('oejskit', 'pytest11',
                                            'pytest_jstests')
    p = make_tests(testdir)

    testreps = []
    def pytest_runtest_logreport(report):
        testreps.append(report)

    testdir.plugins.extend([plugin,
                  {'pytest_runtest_logreport': pytest_runtest_logreport}])

    items, rec = testdir.inline_genitems('-s', p)
    assert len(items) == 2
    item0 = items[0]
    # xxx not completely the right point
    item0.config.pluginmanager.do_configure(item0.config)

    plugin = item0.config.pluginmanager.getplugin("jstests")
    check_clean(plugin)

    # NB if item0 is directly used things explode
    # that's not what looponfails does though
    try:
        # <= 1.1.1
        item1 = item0._fromtrail(item0._totrail(), item0.config)
    except AttributeError:
        rootcol = item0.config._rootcol
        item1 = rootcol.fromtrail(rootcol.totrail(item0))

    item1.config.hook.pytest_runtest_protocol(item=item1)
    assert len(testreps) == 1
    testrep = testreps[0]
    assert testrep.passed, str(testrep)

    # cleanup
    item1.config._setupstate.teardown_all()

    check_clean(plugin)

# xxx test failure
