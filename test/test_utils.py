import py
from oejskit.testing import BrowserTestClass, jstests_suite

class TestUtils(BrowserTestClass):
    jstests_browser_kind = 'supported'
    
    @jstests_suite('test_utils.js')
    def test_inbrowser(self):
        pass
