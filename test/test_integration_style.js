

Tests = {
    test_get_ok: function() {
        var ok = OpenEnd._GET('/')
        ais(ok, "ok\n")
    }
}
