import unittest
from oejskit import unittest_support


class ProjectJSTestSuite(unittest_support.JSTestSuite):

    jstests_browser_specs = {
        'supported': ['firefox', 'iexplore', 'safari']
    }


def ok_root():
    def ok(environ, start_response):
        start_response('200 OK', [('content-type', 'text/plain')])
        return ['ok\n']
    return ok


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=1)
    all = unittest.TestSuite()
    example_suite = ProjectJSTestSuite('jstest_example_supported.js')
    integration_suite = ProjectJSTestSuite('test_integration_style.js',
                                           root=ok_root,
                                           browser_kind='supported')
    all.addTest(example_suite)
    all.addTest(integration_suite)
    runner.run(all)
