/*

Copyright (C) OpenEnd 2007-2009, All rights reserved.
See LICENSE.txt

*/


// helper to do DOM operations achored in the document
function insertTestNode() {
    var body = getFirstElementByTagAndClassName("body")
    var firstName = null
    var testName = null
    var caller = insertTestNode.caller
    while(caller) {
        var name = caller.name || caller.__name__
        if (name) {
            if (!firstName) {
                firstName = name
            }
            if (name.substring(0, 5) == "test_") {
                testName = name
                break
            }
        }
        caller = caller.caller
    }

    var title = SPAN({"style": "color: #1594C2;"}, testName || firstName || "?")
    var testDiv = DIV()

    var cont = DIV({"style": "border: solid 1px #1594C2; margin-bottom: 1em; " }, 
                   title, testDiv)

    appendChildNodes(body, cont)
    return testDiv
}

/* ________________________________________________________________ */

// XXX Windmill has better stuff

function fakeMouseEvent(target, kind, button) {
    var evt
    if(document.createEvent) {
        evt = document.createEvent("MouseEvents")
        evt.initMouseEvent(kind, true, true, window,
                           0, 0, 0, 0, 0, false, false, false,
                           false, button || 0, null)
        target.dispatchEvent(evt)
    } else if(document.createEventObject) {
        evt = document.createEventObject()
        evt.button = button || 0
        target.fireEvent('on'+kind, evt);
    } else {
        throw "Don't know how to fake mouse events in this browser"
    }
    return evt
}

function fakeMouseClick(target) {
    return fakeMouseEvent(target, "click")
}


function fakeHTMLEvent(target, kind) {
    var evt
    if(document.createEvent) {
        evt = document.createEvent("HTMLEvents")
        evt.initEvent(kind, true, true)
        target.dispatchEvent(evt)
    } else if(document.createEventObject) {
        evt = document.createEventObject()
        target.fireEvent('on'+kind, evt);
    } else {
        throw "Don't know how to fake html events in this browser"
    }
    return evt
}

function fakeKeyEvent(target, kind, keyCode, charCode, shiftKey) {
    var evt
    if (charCode == undefined) {
        charCode = keyCode
    }
    if(document.createEvent) {
        if (window.KeyEvent) {
            evt = document.createEvent("KeyEvents")
            evt.initKeyEvent(kind, true, true, window,
			     false, false, shiftKey || false, false,
			     keyCode, charCode)
        } else {
            evt = document.createEvent("Events")
            evt.initEvent(kind, true, true)
            evt.charCode = charCode
            evt.keyCode = keyCode
            evt.shiftKey = shiftKey || false
        }
        target.dispatchEvent(evt)
    } else if(document.createEventObject) {
        evt = document.createEventObject()
        evt.keyCode = keyCode
        if (shiftKey) {
            evt.shiftKey = shiftKey
        }
        target.fireEvent('on'+kind, evt);
    } else {
        throw "Don't know how to fake html events in this browser"
    }
    return evt
}

/* ________________________________________________________________ */

function substitute(substitutions, func) {
    var old_values = {}
    for(var key in substitutions) {
        old_values[key] = eval(key)
        var val = substitutions[key]
        eval(key + ' = val')
    }
    function cleanup(result) {
        for(var key in old_values) {
            var val = old_values[key]
            eval(key + ' = val')
        }
        return result
    }

    var res = null
    try {
        res = func()
        if (res instanceof Deferred) {
            res.addBoth(cleanup)
        }
        return res
    } finally {
        if (!(res instanceof Deferred)) {
            cleanup()
        }
    }
}

/* ________________________________________________________________ */

function _runStages(d, input, i, funcs) {
    if (i >= funcs.length) {
        if (d != null) {
            d.callback(input)
            return
        }
        return input
    }

    var func = funcs[i]
    try {
        var cur = func(input)
    } catch(e) {
        if(d == null) {
            throw e;
        }
        d.errback(e)
        return
    }
    if (cur instanceof Deferred) {
        if (d == null) {
            d = new  Deferred()
            // xxx cleanup
        }
        // xxx errback, both cases
        cur.addCallback(function(v) {
            _runStages(d, v, i+1, funcs)
        })
        cur.addErrback(function(f) {
            d.errback(f)
        })
        return d
    }

    return _runStages(d, cur, i+1, funcs)
}

function staged() {
    return _runStages(null, undefined, 0, arguments) 
}
