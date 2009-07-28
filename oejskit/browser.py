#
# Copyright (C) Open End AB 2009, All rights reserved
# See LICENSE.txt
#
"""
Starting browsers locally and remotely
"""
import sys, os, time, socket, urlparse, hashlib, hmac, binascii
import datetime, optparse

# env configuration and security

def _remote_map(_cached={}):
    if _cached:
        return _cached
    remote_browsers = os.environ.get('JSTESTS_REMOTE_BROWSERS', '')
    remote_map = _cached
    # hostA:portA:browser1,... hostB:portB:...
    for per_host in remote_browsers.split():
        host, port, browsers = per_host.split(':')
        addr = (host, int(port))
        for browser in browsers.split(','):
            remote_map[browser] = addr
    return remote_map

def _gentoken():
    return binascii.hexlify(os.urandom(16))

_token_cache = []
def _read_token():
    if _token_cache:
        return _token_cache[0]
    token = os.environ.get('JSTESTS_REMOTE_BROWSERS_TOKEN')
    if token is None:
        raise RuntimeError("no security token available")
    if token.startswith('file:'):
        token = open(token[len('file:'):], 'r').read().strip()
    token = binascii.unhexlify(token)
    _token_cache.append(token)
    return token

def _nonce():
    return binascii.hexlify(os.urandom(2))+repr(time.time())

def _hmac(cmd_list, nonce):
    token = _read_token()
    txt = nonce+'+'.join(cmd_list)
    return hmac.new(token, txt, hashlib.sha1).hexdigest()

def _bundle_with_hmac(cmd_list, nonce):
    assert cmd_list
    return ' '.join(cmd_list+[_hmac(cmd_list, nonce)])

def _parse_authorized(line, nonce):
    bits = line.split()
    if not bits:
        return None
    cmd_list = bits[:-1]
    token = bits[-1]
    expected = _hmac(cmd_list, nonce)
    if token != expected:
        return None
    return cmd_list
    

# local and do()

BROWSERS = ['firefox', 'iexplore', 'safari']

_win_extra = {
    'firefox': ('mozilla firefox', 0),
    'iexplore': ('internet explorer', 1)
    }

class _WinToTop(object):

    def _windows(self):
        import win32gui
        res = set()
        def cb(w, _):
            text = win32gui.GetWindowText(w)
            if text.lower().endswith(self.sig):
                res.add(w)
        win32gui.EnumWindows(cb, None)
        return res

    def __init__(self, name):
        self._do = bool(os.environ.get('JSTESTS_BROWSERS_WIN_TO_TOP'))
        self.sig, self.expected_delta = _win_extra[name]
        self._before = None

    def before(self):
        if not self._do:
            return
        self._before = self._windows()

    def to_top(self):
        if not self._do:
            return
        
        import win32gui
        
        before = self._before
        start = time.time()
        expected_delta = self.expected_delta
        while time.time() - start < 10:
            after = self._windows()
            delta = after - before
            if after and len(delta) >= expected_delta:
                break
            time.sleep(1)
        got = delta or after
        if got:
            w = list(got)[0]
            win32gui.BringWindowToTop(w)

def _win_start(name, url):
    import win32api
    to_top = _WinToTop(name)
    to_top.before()    
    win32api.ShellExecute(0, None, name, url, None, 1) # SW_SHOWNORMAL
    to_top.to_top()
        

def start_browser_local(name, url, manual=False):
    if name not in BROWSERS:
        return
    if sys.platform == 'win32':
        _win_start(name, url)
    else:
        if sys.platform == 'darwin':
            name = "open -a " + name.title()
        start_cmd = "%s %s &" % (name, url)
        print start_cmd
        os.system(start_cmd)

def cleanup_browser_local(name):    
    if sys.platform != 'win32':
        return
    if name not in BROWERS:
        return    
    img = name+".exe"

    def nt_check_for_running(img):
        return img in os.popen('tasklist'
                               ' /fi "username eq %s"'
                               ' /fi "imagename eq %s"' % (
                                os.environ['USERNAME'], img)).read()

    os.system('taskkill /im %s '
              ' /fi "username eq %s"' % (img, os.environ['USERNAME']))
    t = 0
    # seems that firefox3 takes a while to die on trokk
    while nt_check_for_running(img) and t < 3:
        time.sleep(1)
        t += 1
    if nt_check_for_running(img):
        os.system('taskkill /f /im %s '
                  ' /fi "username eq %s"' % (img, os.environ['USERNAME']))


def do(cmd_list, suite):
    cmd = cmd_list[0]
    if cmd not in suite:
        return
    cmd_func = suite[cmd]
    if cmd == 'cleanup':
        for name in cmd_list[1:]:
            cmd_func(name)
    elif cmd == 'start':
        name = cmd_list[1]
        url = cmd_list[2]
        manual = False
        if len(cmd_list) > 3:
            manual = cmd_list[3] == 'y'
        cmd_func(name, url, manual)
    elif cmd == 'server':
        port = 0
        parser = optparse.OptionParser()
        parser.add_option('--log', type='string')
        parser.add_option('--win-to-top', action='store_true', default=False)
        flags, args = parser.parse_args(cmd_list[1:])
        if len(args) > 0:
            port = int(args[0])
        if 'JSTESTS_REMOTE_BROWSERS_TOKEN' not in os.environ:
            if len(args) > 1:
                tok = args[1]
            else:
                tok = _gentoken()
                print 'JSTESTS_REMOTE_BROWSERS_TOKEN=%s' % tok
            os.environ['JSTESTS_REMOTE_BROWSERS_TOKEN'] = tok
        if flags.win_to_top:
            os.environ['JSTESTS_BROWSERS_WIN_TO_TOP'] = '1'
        cmd_func(port, log=flags.log)
    elif cmd in ('shutdown-servers', 'gentoken'):
        cmd_func()
    else:
        raise RuntimeError("unknown command: %s" % cmd_list)

# server

LOCAL = {
    'start': start_browser_local,
    'cleanup': cleanup_browser_local
    }

# xxx timeout
def server(port, log):
    if log:
        log = open(log, 'a+')
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(5)
    print "serving browsers on %s..." % s.getsockname()[1]
    try:
        while True:
            cl, addr = s.accept()
            f = cl.makefile("r+")
            try:
                nonce = _nonce()
                f.write(nonce+"\n")
                f.flush()
                line = f.readline()
                # naive white space treatmeant                
                cmd_list = _parse_authorized(line, nonce)
                if cmd_list is None:
                    continue
                if log:
                    log.write("[%s] %s\n" % (datetime.datetime.now(),
                                             ' '.join(cmd_list)))
                if cmd_list[0] == 'shutdown':
                    f.write("ok\n")
                    return
                do(cmd_list, LOCAL)
                f.write("ok\n")
            finally:
                f.close()
                cl.close()
    finally:
        s.close()
        if log:
            log.close()

# interface

def _check_remote(name):
    remote_map = _remote_map()
    return remote_map.get(name)

def _send_cmd(addr, cmd_list):
    s = socket.socket()
    s.settimeout(15)
    s.connect(addr)
    f = s.makefile("w+", 0)
    try:
        nonce = f.readline().strip()
        msg = _bundle_with_hmac(cmd_list, nonce)
        f.write(msg+"\n")
        ok = f.readline()
        if ok != "ok\n":
            raise RuntimeError("invoking %s remotely failed" % cmd_list)
    finally:
        f.close()
        s.close()
            
def _invoke(cmd_list):
    name = cmd_list[1]
    addr = _check_remote(name)
    if addr is None:
        do(cmd_list, LOCAL)
    else:
        # invoke remotely
        def delocalhost(part):
            if part.startswith('http'):
                urlparts = list(urlparse.urlsplit(part))
                if urlparts[1].startswith('localhost'):
                    # xxx not ideal
                    urlparts[1] = urlparts[1].replace('localhost', socket.gethostname())
                part = urlparse.urlunsplit(urlparts)

            return part
        cmd_list = map(delocalhost, cmd_list)
        _send_cmd(addr, cmd_list)

def check_browser(name):
    if _check_remote(name): # assume remote implies supported
        return True
    # xxx naive
    if name == 'iexplore' and sys.platform != 'win32':
        return False
    if name == 'safari' and sys.platform != 'darwin':
        return False
    return True

def start_browser(name, url, manual=False):
    if manual:
        print "open", url
        raw_input()
    _invoke(['start', name, url])

def cleanup_browser(name):
    _invoke(['cleanup', name])

def shutdown_servers():
    remote_map = _remote_map()
    addrs = set(remote_map.values())
    for addr in addrs:
        _send_cmd(addr, ['shutdown'])

def gentoken():
    print _gentoken()
                      

CMDLINE = {
    'cleanup': cleanup_browser,
    'start': start_browser,
    'server': server,
    'shutdown-servers': shutdown_servers,
    'gentoken': gentoken
    }
    
if __name__ == "__main__":
    do(sys.argv[1:], CMDLINE)
