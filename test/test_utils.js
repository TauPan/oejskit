
Substitute = {}
substitute_me = null

Tests = {
test_insertTestNode: function() {
    var node = insertTestNode()
    aok(node)
    ais(node.tagName, "DIV")
    aok(node.ownerDocument === document)
    var parent = node.parentNode
    while (parent) {
        if (parent === document.body) {
            return
        }
        parent = parent.parentNode
    }
    aok(false, "not inside the body")
},

test_fakeMouseClickEvent: function() {
    var node = insertTestNode()

    var clicked
    node.onclick = function(evt) { // firefox
        if(evt) {
            clicked = evt
        } else if(window.event) { // ie
            clicked = window.event
        }
    }
    ais(clicked, undefined)
    var event = fakeMouseClick(node)
    ais(clicked, event)
},

test_fakeMouseEvent: function() {
    var node = insertTestNode()

    var button
    node.oncontextmenu = function(evt) { // firefox
        if(evt) {
            button = evt.button
        } else if(window.event) { // ie
            button = window.event.button
        }
    }
    ais(button, undefined)
    var event = fakeMouseEvent(node, "contextmenu", 2)
    ais(button, 2)
},

test_fakeHTMLEvent: function() {
    var ta = MochiKit.DOM.TEXTAREA()
    MochiKit.DOM.appendChildNodes(insertTestNode(), ta)

    var triggered = false
    ta.onchange = function() {
        triggered = true
    }

    fakeHTMLEvent(ta, "change")

    aok(triggered)
},

test_fakeKeyEvent: function() {
    var ta = MochiKit.DOM.TEXTAREA()
    MochiKit.DOM.appendChildNodes(insertTestNode(), ta)

    var keyCode
    var charCode
    var shiftKey
    ta.onkeypress = function(event) {
	event = event || window.event // window.event for ie
        keyCode = event.keyCode
        charCode = event.charCode
        shiftKey = event.shiftKey
    }

    var ff = !!document.createEvent

    fakeKeyEvent(ta, "keypress", 65)
    ais(keyCode, 65)
    if (ff) {
        ais(charCode, 65)
    }
    ais(shiftKey, false)

    fakeKeyEvent(ta, "keypress", 9, 0)
    ais(keyCode, 9)
    if (ff) {
        ais(charCode, 0)
    }
    ais(shiftKey, false)

    fakeKeyEvent(ta, "keypress", 9, 0, true)
    ais(keyCode, 9)
    if (ff) {
        ais(charCode, 0)
    }
    ais(shiftKey, true)
},


test_substitute: function() {
    Substitute.x = 27
    substitute_me = "foo"

    var values = []
    var res = substitute({"Substitute.x" : 42, "substitute_me": "bar"}, function() {
        values.push([Substitute.x, substitute_me])
        return "return value"
    })
    ais(res, "return value")
    aisDeeply(values, [[42, "bar"]])
    ais(Substitute.x, 27)
    ais(substitute_me, "foo")

    var values = []
    var err = araises(function() {
        substitute({"Substitute.x" : 42, "substitute_me": "bar"}, function() {
            values.push([Substitute.x, substitute_me])
            throw "Error!"
        })
    })

    ais(err, "Error!")
    aisDeeply(values, [[42, "bar"]])
    ais(Substitute.x, 27)
    ais(substitute_me, "foo")

},

test_substitute_deferred: function() {
    Substitute.x = 27
    substitute_me = "foo"

    var values = []
    var d = new MochiKit.Async.Deferred()
    var res = substitute({"Substitute.x" : 42, "substitute_me": "bar"}, function() {
        values.push([Substitute.x, substitute_me])
        return d
    })

    aok(res === d)
    aisDeeply(values, [[42, "bar"]])
    ais(Substitute.x, 42)
    ais(substitute_me, "bar")

    d.callback("return value")
    ais(Substitute.x, 27)
    ais(substitute_me, "foo")

    var d = new MochiKit.Async.Deferred()
    var res = substitute({"Substitute.x" : 42, "substitute_me": "bar"}, function() {
        return d
    })
    d.errback("error")
    ais(Substitute.x, 27)
    ais(substitute_me, "foo")
},

/*
test_testing__atomic_t: function() {
    ais(testing_atomic_t('lower'), 'LOWER')
    ais(testing_atomic_t('Upper'), 'UPPER')

    ais(testing_atomic_t('lower %s'), 'LOWER %s')
    ais(testing_atomic_t('lower %(fooBar)s'), 'LOWER %(fooBar)s')
    ais(testing_atomic_t('lower %(foo)s %(bar)s'), 'LOWER %(foo)s %(bar)s')

    ais(_t('lower', undefined, testing_atomic_t), 'LOWER')
    ais(_t('lower %s', 'foo', testing_atomic_t), 'LOWER foo')
},
*/

test_staged: function() {
    var res = staged(function() {
        return 42
    })
    ais(res, 42)

    res = staged(
        function() {
            return 21
        },
        function(v) {
            return 2*v
        }
      )
    ais(res, 42)

    var x = null
    var y = 0
    try {
    res = staged(
        function() {
            throw "Bomb";
            return 21
        },
        function(v) {
            y = 1
        }
      )
    } catch(e) {
        x = e
    }
    ais(x, "Bomb")
    ais(y, 0)

    var x = null
    var y = 0
    try {
    res = staged(
        function() {
            y = 1
        },
        function(v) {
            throw "Bomb"
        }
      )
    } catch(e) {
        x = e
    }
    ais(x, "Bomb")
    ais(y, 1)
},

test_staged_with_deferred: function() {
    var dres = staged(function() {
        return MochiKit.Async.succeed(43)
    })
    aok(dres instanceof MochiKit.Async.Deferred)
    var  res
    dres.addCallback(function(v) { res = v})
    ais(res, 43)

    dres = staged(
        function() {
            return MochiKit.Async.succeed(21)
        },
        function(v) {
            return 2*v+2
        }
      )
    aok(dres instanceof MochiKit.Async.Deferred)
    dres.addCallback(function(v) { res = v})
    ais(res, 44)

    dres = staged(
        function() {
            return 21
        },
        function(v) {
            return MochiKit.Async.succeed(2*v)
        }
      )
    aok(dres instanceof MochiKit.Async.Deferred)
    dres.addCallback(function(v) { res = v})
    ais(res, 42)

    dres = staged(
        function() {
            return MochiKit.Async.succeed(20)
        },
        function(v) {
            return MochiKit.Async.succeed(2*v)
        }
      )
    aok(dres instanceof MochiKit.Async.Deferred)
    dres.addCallback(function(v) { res = v})
    ais(res, 40)

    var w
    dres = staged(
        function() {
            w = new MochiKit.Async.Deferred()
            w.addCallback(function(x) {
                return MochiKit.Async.succeed(x+3)
            })
            return w
        },
        function(v) {
            return MochiKit.Async.succeed(2*v)
        }
      )
    aok(dres instanceof MochiKit.Async.Deferred)
    dres.addCallback(function(v) { res = v})
    w.callback(19)
    ais(res, 44)
},

test_staged_with_deferred_failures: function() {
    var x = null
    var y = 1
    var dres = staged(
        function() {
            y = 1
            return MochiKit.Async.succeed(0)
        },
        function(v) {
            throw "Bomb"
        }
    )
    aok(dres instanceof MochiKit.Async.Deferred)
    ais(y, 1)
    dres.addErrback(function(v) { x = v })
    aok(x instanceof MochiKit.Async.GenericError)
    ais(x.message, 'Bomb')

    var x = null
    var y = 1
    dres = staged(
        function() {
            y = 1
            return MochiKit.Async.fail("Bomb")
        },
        function(v) {
            y = 2
        }
    )
    aok(dres instanceof MochiKit.Async.Deferred)
    ais(y, 1)
    dres.addErrback(function(v) { x = v })
    aok(x instanceof MochiKit.Async.GenericError)
    ais(x.message, 'Bomb')
},

test_staged_applied: function() {
    var x = null
    return staged(
        function() {
            x = 3
            return MochiKit.Async.succeed(4)
        },
        function(v) {
            ais(v, 4)
            ais(x, 3)
        })
}

}
