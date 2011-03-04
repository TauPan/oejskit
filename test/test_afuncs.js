

Tests = {

test_araises: function() {
    function bomb(crash) {
        if (crash) {
            throw "crash and burn"
        }
    }

    var e = araises(bomb, true)

    ais(e, "crash and burn")


    var err = null
    try {
        araises(bomb, false)
    } catch(e) {
        err = e
    }

    aok(err instanceof Testing.Fail)
    var msg = err.message
    if (bomb.name) {
        aok(msg.indexOf('bomb') != -1)
    }
},

test_aisDeeply: function() {
    aisDeeply({}, {})

    var o = {}
    aisDeeply(o,o)

    aisDeeply({'a': 1, 'b': 2}, {'a': 1, 'b': 2})

    aisDeeply({'a': 1, 'b': undefined}, {'a': 1})

    var o = {'a': 1, 'b': 3}
    aisDeeply(o, o)

    araises(aisDeeply, {'a': 1}, {'a': 1, 'c': 3})

    araises(aisDeeply, {'a': 1, 'c': 3}, {'a': 1})

    araises(aisDeeply, {'a': 1, 'b': undefined}, {'a': 1, 'c': 3})

    araises(aisDeeply, {'a': 1, 'c': 3}, {'a': 1, 'b': undefined})

    var l = [1, 2]
    aisDeeply(l, l)

    var x = []
    x.push(x)
    aisDeeply(x, x)

    var y = []
    y.push(y)
    aisDeeply(x, y)

    var a = [l, l]
    aisDeeply(a, [[1, 2], [1, 2]])

    var a = [new Date(1000)]
    aisDeeply(a, [new Date(1000)])
    araises(aisDeeply, a, [new Date(10000)])
}

}
