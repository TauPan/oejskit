

Tests = {
    test_get_ok: function() {
        var ok = OpenEnd._GET('/integration') // naive work around IE caching issues
        ais(ok, "ok\n")
    }
}
