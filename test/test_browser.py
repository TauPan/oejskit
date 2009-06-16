import py, os, binascii

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
        broken_msg = msg[:-1] + "%x" % (15-int(msg[-1], 16))
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
    
    
