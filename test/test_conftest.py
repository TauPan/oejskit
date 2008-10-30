

def test_g():
    def check(x):
        assert x in (7, 8, 9)
    for x in range(7, 10):
        yield check, x

def test_g_explicit():
    def check(x):
        assert x in (7, 8, 9)
    for x in range(7, 10):
        yield str(x), check, x
test_g_explicit.explicit_names = True
