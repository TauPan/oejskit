
Tests = {

test_ff35_iteration_over_object: function() {
    // this explodes if we have global leak detection on FF3.5
    var o = { a: 1, b : 2}
    var ks = keys(o)
    ais(ks.length, 2)
}

}