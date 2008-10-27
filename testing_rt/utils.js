
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

    var title = SPAN({"style": "color: red;"}, testName || firstName || "?")
    var testDiv = DIV()

    var cont = DIV({"style": "border: solid 1px red; margin-bottom: 1em; " }, 
                   title, testDiv)

    appendChildNodes(body, cont)
    return testDiv
}

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
        evt = document.createEvent("KeyEvents")
        evt.initKeyEvent(kind, true, true, window,
			 false, false, shiftKey || false, false,
			 keyCode, charCode)
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

function substitute(substitutions, func) {
    var old_values = {}
    for(var key in substitutions) {
        old_values[key] = eval(key)
        var val = substitutions[key]
        eval(key + ' = val')
    }
    try {
        return func()
    } finally {
        for(var key in old_values) {
            var val = old_values[key]
            eval(key + ' = val')
        }
    }
}

/* ?
function testing_atomic_t(s) {
    var format = new RegExp('%(?:\\((\\w+)\\))?s', 'g')
    var isFormat = format.exec(s)
    var memo
    var armored = s

    if (isFormat) {
        var c = 0
        memo = {}
        function armor(placeholder, name) {
            if (name) {
                var armored_placeholder = "%("+c+")s"
                memo[c++] = name
                return armored_placeholder

            }
            return "%s"
        }
        armored = s.replace(format, armor)
    }
    var translated  = armored.toUpperCase()
    if (isFormat) {
        function unarmor(placeholder, index) {
            if(index) {
                var name = memo[index]
                return "%("+name+")s"
            }
            return "%s"
        }
        translated = translated.replace(/%(?:\((\w+)\))?S/g, unarmor)
    }
    return translated
}

_atomic_t = testing_atomic_t
*/

