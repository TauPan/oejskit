

Tests = {
    test_sanity: function() {
        var ok = OpenEnd._GET('/')
        ais(ok, "ok\n")
    }
}
