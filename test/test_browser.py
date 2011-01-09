import py, sys, os, binascii, tempfile, shutil

from oejskit import browser

SECRET = 'R\x15\x0f\xca\x89\xc1EKd\xda,\xf9/\xc2\x8c\x9b'


class TestSecurityFunctions():

    def setup_class(cls):
        cls.old_value = os.environ.get('JSTESTS_REMOTE_BROWSERS_TOKEN')
        del browser._token_cache[:]
        os.environ['JSTESTS_REMOTE_BROWSERS_TOKEN'] = binascii.hexlify(SECRET)

    def teardown_class(cls):
        del browser._token_cache[:]
        if cls.old_value is None:
            del os.environ['JSTESTS_REMOTE_BROWSERS_TOKEN']
        else:
            os.environ['JSTESTS_REMOTE_BROWSERS_TOKEN'] = cls.old_value

    def test__read_token(self):
        token = browser._read_token()
        assert token == SECRET
        token = browser._read_token()
        assert token == SECRET

    def test_message_handling(self):
        nonce = browser._nonce()
        cmd_list = ['start', 'firefox', 'http://example.com']
        msg = browser._bundle_with_hmac(cmd_list, nonce)

        parsed = browser._parse_authorized(msg, nonce)

        assert parsed == cmd_list

        # broken hmac
        broken_msg = msg[:-1] + "%x" % (15 - int(msg[-1], 16))
        assert broken_msg != msg

        parsed = browser._parse_authorized(broken_msg, nonce)
        assert parsed is None

        # junk
        parsed = browser._parse_authorized("", nonce)
        assert parsed is None

        parsed = browser._parse_authorized("start", nonce)
        assert parsed is None

        parsed = browser._parse_authorized("start ff", nonce)
        assert parsed is None


class TestCheckBrowser(object):

    def test_on_path(self, tmpdir, monkeypatch):
        f = os.open(os.path.join(str(tmpdir), 'xbrowser.exe'),
                    os.O_CREAT, 0700)
        os.close(f)
        monkeypatch.setenv('PATH', str(tmpdir), prepend=os.pathsep)

        assert browser.check_browser('xbrowser.exe') == 'xbrowser.exe'

        assert not browser.check_browser('not-existent-browser.exe')

    def test_win32_registry(self):
        if sys.platform != 'win32':
            py.test.skip("windows only")
        assert browser.check_browser('iexplore') == 'iexplore'
        assert browser.check_browser('IEXPLORE.exe') == 'IEXPLORE.exe'

    def test_win32_fallback(self, tmpdir, monkeypatch):
        if sys.platform != 'win32':
            py.test.skip("windows only")
        tmpdir.ensure('Safari', dir=1).join('Safari.exe').write("")
        old__listdir = browser._listdir
        def test_listdir(dir):
            assert os.path.isdir(dir)
            return old__listdir(str(tmpdir))
        monkeypatch.setattr(browser, '_listdir', test_listdir)
        res = browser.check_browser('safari')
        assert res
        assert res.lower() == str(tmpdir.join('Safari')
                                        .join('Safari.exe')).lower()

    def test_safari_on_mac(self):
        if sys.platform != 'darwin':
            py.test.skip("Mac OS X only")
        res = browser.check_browser('safari')
        assert res

        res = browser.check_browser('Safari')
        assert res

        assert res == "open -a Safari.app"


class TestStartBrowser(object):

    def test_nonexistent_browser(self):
        py.test.raises(browser.Error, browser.start_browser_local,
                                      'nonExistent',
                                      'http://localhost:99')
