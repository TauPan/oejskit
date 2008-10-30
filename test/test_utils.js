
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
    var ta = TEXTAREA()
    appendChildNodes(insertTestNode(), ta)

    var triggered = false
    ta.onchange = function() {
        triggered = true
    }

    fakeHTMLEvent(ta, "change")    

    aok(triggered)
},

test_fakeKeyEvent: function() {
    var ta = TEXTAREA()
    appendChildNodes(insertTestNode(), ta)

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

}

/*test_testing__atomic_t: function() {
    ais(testing_atomic_t('lower'), 'LOWER')
    ais(testing_atomic_t('Upper'), 'UPPER')

    ais(testing_atomic_t('lower %s'), 'LOWER %s')
    ais(testing_atomic_t('lower %(fooBar)s'), 'LOWER %(fooBar)s')
    ais(testing_atomic_t('lower %(foo)s %(bar)s'), 'LOWER %(foo)s %(bar)s')

    ais(_t('lower', undefined, testing_atomic_t), 'LOWER')
    ais(_t('lower %s', 'foo', testing_atomic_t), 'LOWER foo')
}*/

}
