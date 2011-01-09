import py
from oejskit.testing import BrowserTestClass, jstests_suite


class TestAFuncs(BrowserTestClass):
    jstests_browser_kind = 'supported'

    @jstests_suite('test_afuncs.js')
    def test_inbrowser(self):
        return
