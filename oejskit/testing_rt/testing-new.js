/*

Copyright (C) OpenEnd 2007-2009, All rights reserved.
See LICENSE.txt

Parts are derivative from MochiKit SimpleTest
Copyright (c) 2005 Bob Ippolito. All rights reserved.

*/

// XXX obsolete style
if (typeof(JSAN) != "undefined") {
    JSAN.use("MochiKit.Base")
    JSAN.use("MochiKit.Iter")
    JSAN.use("MochiKit.Async")
    JSAN.use("MochiKit.Style")
    JSAN.use("MochiKit.DOM", ":all")
}



Testing = {'_collected': null, '_report': null, '_ns': null}

Testing._init =  function () {
    var head = getFirstElementByTagAndClassName("HEAD")
    appendChildNodes(head, createDOM("LINK", {'rel': "stylesheet", 'type': "text/css",
        'href': "/lib/mochikit/tests/SimpleTest/test.css"}))
}

Testing._init()

Testing.collect = function() {
    if (Testing._collected != null) {
	return Testing._collected
    }
    
    var testNames = []
    Testing._collected = testNames
    Testing._passed = 0
    Testing._failed = 0

    if (window.Tests) {
	var cands = keys(window.Tests)
	cands.sort()
        forEach(cands, function(topName) {
            if (topName.substring(0, 5) == 'test_') {
                testNames.push(topName)
            }
        })
    }

    return testNames

}

Testing._toggle = function(el) {
    if (MochiKit.Style.getStyle(el, 'display') == 'block') {
        el.style.display = 'none';
    } else {
        el.style.display = 'block';
    }
};


Testing._toggleByClass = function (cls) {
    var elems = getElementsByTagAndClassName('div', cls);
    MochiKit.Base.map(Testing._toggle, elems);
};

Testing._startReport = function() {
    if (Testing._report != null) return;

    var togglePassed = A({'href': '#'}, "Toggle passed tests");
    var toggleFailed = A({'href': '#'}, "Toggle failed tests");
    togglePassed.onclick = MochiKit.Base.partial(Testing._toggleByClass, 'test_ok');
    toggleFailed.onclick = MochiKit.Base.partial(Testing._toggleByClass, 'test_not_ok');
    var body = document.getElementsByTagName("body")[0];
    var firstChild = body.childNodes[0];
    var addNode;
    if (firstChild) {
        addNode = function (el) {
            body.insertBefore(el, firstChild);
        };
    } else {
        addNode = function (el) {
            body.appendChild(el)
        };
    }
    addNode(togglePassed);
    addNode(SPAN(null, " "));
    addNode(toggleFailed);
    Testing._report =  DIV({'class': 'tests_report'},
        DIV()
    );
    addNode(Testing._report)
};

Testing._updateSummary = function() {
    var summary = Testing._report.childNodes[0]
    var passed = Testing._passed
    var failed = Testing._failed
    var summary_class = ((failed == 0) ? 'all_pass' : 'some_fail');
    swapDOM(summary,
            DIV({'class': 'tests_summary ' + summary_class},
		DIV({'class': 'tests_passed'}, "Passed: " + passed),
		DIV({'class': 'tests_failed'}, "Failed: " + failed))
	    )    
}


Testing.outcome = function (condition, name, diag, leakedNames) {
    var test = {'result': !!condition, 'name': name, 'diag': diag || ""}
                
    var cls, msg;
    if (test.result) {
        Testing._passed++;
        cls = "test_ok";
        msg = "ok - " + test.name;
    } else {
        Testing._failed++;
        cls = "test_not_ok";
        msg = "not ok - " + test.name + " " + test.diag;
    }
    Testing._startReport()
    Testing._report.appendChild(DIV({"class": cls}, msg))
    Testing._updateSummary()

    if (leakedNames != undefined) {
        test.leakedNames = leakedNames
    }

    return test
}


Testing._EMPTY = {}
Testing._FAILSKIP = {name: null, message: null, label: null}

Testing._globalNames = function() {
    if (window.navigator && 
        window.navigator.appName == "Microsoft Internet Explorer" ||
         // workaround https://bugzilla.mozilla.org/show_bug.cgi?id=504078
         // turning this off on FF3.5
	 /Firefox\/3\.5/.exec(window.navigator.userAgent)) {
        // finding the global names is unreliable on IE :(
        return []
    }
    // workaround obscure FF behavior, these two attrs
    // appear only lazily (maybe others?)
    window.location
    window.addEventListener
    var names =  keys(window)
    // Firebug attributes + FF3.5+
    return names.concat(['_firebug','_FirebugConsole', 'getInterface'])
}

Testing.runOne = function (which, done) {
    if (Testing._ns == null) {
        var ns = {}
        Testing._ns = ns
        forEach(Testing._globalNames(), function(name) {
            ns[name] = null
        })
    }
    var func = window.Tests[which]
    if (func.name == undefined || func.name == "") {
	func.name = which
	func.__name__ = which
    }
    var defer = maybeDeferred(func)
    defer.addCallback(function() {
        var leakedNames = filter(function(name) {return !(name in Testing._ns)},
                                     Testing._globalNames())
	return Testing.outcome(true, which, "", leakedNames)
    })
    defer.addErrback(function(err) {
        var k
        var s = "FAILED:"
        var skip = Testing._EMPTY
        if (err instanceof Testing.Fail) {
            var label = err.label
            s += " " + err.message
            skip = Testing._FAILSKIP
        }
        s += '\n'
        for (k in err) {
            if (k in skip) continue;
	    s +=  k + ": " + err[k] + "\n"
        }
        return Testing.outcome(false, which, s, [])
    })
    defer.addBoth(function (outcome) {
	done(outcome)
    })
}


Testing.Fail = function(label, diag) {
    this.name = "Fail"
    this.message = diag
    this.label = label
    this.stack = new Error().stack
}
Testing.Fail.prototype = new Error()

Testing._contextualize = function(func, name) {
    if (func.caller) {
	var caller = func.caller
        return name + ' in ' + (caller.name || caller.__name__ || "?")
    }
    return name
}

Testing.aok = function(cond, name, diag) {
    name = Testing._contextualize(Testing.aok, name || 'ok')
    if (cond) {
        Testing.outcome(true, name)
        return
    }
    throw new Testing.Fail(name, diag || "")
}


Testing.ais = function(a, b, name) {
    var diag = repr(a) + " == " + repr(b)
    name = Testing._contextualize(Testing.ais, name || 'is')
    if (a == b) {
        Testing.outcome(true, name +": "+diag)
        return
    }
    throw new Testing.Fail(name, diag)
}

/* apred araises*/

aok = Testing.aok
ais = Testing.ais


/* aisDeeply */

Testing.DNE = {dne: 'Does not exist'};
Testing.LF = "\r\n";
Testing._isRef = function (object) {
    var type = typeof(object);
    return type == 'object' || type == 'function';
};

Testing._typeOf = function (object) {
    var c = Object.prototype.toString.apply(object);
    var name = c.substring(8, c.length - 1);
    if (name != 'Object') return name;
    // It may be a non-core class. Try to extract the class name from
    // the constructor function. This may not work in all implementations.
    if (/function ([^(\s]+)/.test(Function.toString.call(object.constructor))) {
        return RegExp.$1;
    }
    // No idea. :-(
    return name;
};

Testing._isa = function (object, clas) {
    return Testing._typeOf(object) == clas;
};

Testing._deepCheck = function (e1, e2, stack, seen) {
    var ok = false;
    // Either they're both references or both not.
    var sameRef = !(!Testing._isRef(e1) ^ !Testing._isRef(e2));
    if (e1 == null && e2 == null) {
        return true;
    } else if (e1 != null ^ e2 != null) {
	;
    } else if (e1 == Testing.DNE ^ e2 == Testing.DNE) {
	;
    } else if (sameRef && e1 == e2) {
        // Handles primitives and any variables that reference the same
        // object, including functions.
        return true
    } else if (Testing._isa(e1, 'Array') && Testing._isa(e2, 'Array')) {
        return Testing._eqArray(e1, e2, stack, seen);
    } else if (Testing._isa(e1, 'Date') && Testing._isa(e2, 'Date')) {
	return e1.valueOf() == e2.valueOf()
    } else if (typeof e1 == "object" && typeof e2 == "object") {
        return Testing._eqAssoc(e1, e2, stack, seen);
    } else {
        // If we get here, they're not the same (function references must
        // always simply rererence the same function).
    }
    stack.push({ vals: [e1, e2] });
    return false;
};

Testing._eqArray = function (a1, a2, stack, seen) {
    // Return if they're the same object.
    if (a1 == a2) return true;

    // JavaScript objects have no unique identifiers, so we have to store
    // references to them all in an array, and then compare the references
    // directly. It's slow, but probably won't be much of an issue in
    // practice. Start by making a local copy of the array to as to avoid
    // confusing a reference seen more than once (such as [a, a]) for a
    // circular reference.
    for (var j = 0; j < seen.length; j++) {
        if (seen[j][0] == a1) {
            if(seen[j][1] == a2) return true
        }
    }

    // If we get here, we haven't seen a1 before, so store it with reference
    // to a2.
    seen.push([ a1, a2 ]);

    var ok = true;
    // Only examines enumerable attributes. Only works for numeric arrays!
    // Associative arrays return 0. So call _eqAssoc() for them, instead.
    var max = a1.length > a2.length ? a1.length : a2.length;
    if (max == 0) return Testing._eqAssoc(a1, a2, stack, seen);
    for (var i = 0; i < max; i++) {
        var e1 = i > a1.length - 1 ? Testing.DNE : a1[i];
        var e2 = i > a2.length - 1 ? Testing.DNE : a2[i];
        stack.push({ type: 'Array', idx: i, vals: [e1, e2] });
        if (ok = Testing._deepCheck(e1, e2, stack, seen)) {
            stack.pop();
        } else {
            break;
        }
    }
    return ok;
};

Testing._eqAssoc = function (o1, o2, stack, seen) {
    // Return if they're the same object.
    if (o1 == o2) return true;

    // JavaScript objects have no unique identifiers, so we have to store
    // references to them all in an array, and then compare the references
    // directly. It's slow, but probably won't be much of an issue in
    // practice. Start by making a local copy of the array to as to avoid
    // confusing a reference seen more than once (such as [a, a]) for a
    // circular reference.
    seen = seen.slice(0);
    for (var j = 0; j < seen.length; j++) {
        if (seen[j][0] == o1) {
            if(seen[j][1] == o2) return true
        }
    }

    // If we get here, we haven't seen o1 before, so store it with reference
    // to o2.
    seen.push([ o1, o2 ]);

    // They should be of the same class.

    var ok = true;
    // Only examines enumerable attributes.
    var o1Size = 0; for (var i in o1) if (o1[i] != undefined) o1Size++;
    var o2Size = 0; for (var i in o2) if (o2[i] != undefined) o2Size++;
    var bigger = o1Size > o2Size ? o1 : o2;
    for (var i in bigger) {
        var e1 = o1[i] == undefined ? Testing.DNE : o1[i];
        var e2 = o2[i] == undefined ? Testing.DNE : o2[i];
        stack.push({ type: 'Object', idx: i, vals: [e1, e2] });
        if (ok = Testing._deepCheck(e1, e2, stack, seen)) {
            stack.pop();
        } else {
            break;
        }
    }
    return ok;
};

Testing._formatStack = function (stack) {
    var variable = '$Foo';
    for (var i = 0; i < stack.length; i++) {
        var entry = stack[i];
        var type = entry['type'];
        var idx = entry['idx'];
        if (idx != null) {
            if (/^\d+$/.test(idx)) {
                // Numeric array index.
                variable += '[' + idx + ']';
            } else {
                // Associative array index.
                idx = idx.replace(/'/g, "\\'");
                variable += "['" + idx + "']";
            }
        }
    }

    var vals = stack[stack.length-1]['vals'].slice(0, 2);
    var vars = [
        variable.replace('$Foo',     'got'),
        variable.replace('$Foo',     'expected')
    ];

    var out = "Structures begin differing at:" + Testing.LF;
    for (var i = 0; i < vals.length; i++) {
        var val = vals[i];
        if (val == null) {
            val = 'undefined';
        } else {
             val == Testing.DNE ? "Does not exist" : "'" + val + "'";
        }
    }

    out += vars[0] + ' = ' + vals[0] + Testing.LF;
    out += vars[1] + ' = ' + vals[1] + Testing.LF;
    
    return '    ' + out;
};


Testing.aisDeeply = function (it, as, name) {
    name = Testing._contextualize(Testing.aisDeeply, name || 'isDeeply')
    // ^ is the XOR operator.
    if (Testing._isRef(it) ^ Testing._isRef(as)) {
        // One's a reference, one isn't.
	var diag = repr(it) + " type mismatches " + repr(as)
	Testing.aok(false, name, diag)
    } else if (!Testing._isRef(it) && !Testing._isRef(as)) {
        // Neither is an object.
        Testing.ais(it, as, name);
    } else {
        // We have two objects. Do a deep comparison.
        var stack = [], seen = [];
        if ( Testing._deepCheck(it, as, stack, seen)) {
            Testing.aok(true, name);
        } else {
            Testing.aok(false, name, Testing._formatStack(stack));
        }
    }
};

aisDeeply = Testing.aisDeeply

Testing.araises = function(bomb /* arguments */ ) {
    name = Testing._contextualize(Testing.araises, 'raises')
    var unexpected = {}
    try {
        bomb.apply(null, Array.prototype.slice.call(arguments, 1))
        throw unexpected
    } catch(err) {
        if (err === unexpected) {
            aok(false, name, (bomb.name ||bomb.__name__||"?") + " did not raise")
        }
        return err
    }
}

araises = Testing.araises

// deferred helpers
function d_try(d, f) {
    try {
	return f()
    } catch(e) {
	d.errback(e)
    }
}

function d_fulfill(d, f) {
   var r
   try {
	r = f()
    } catch(e) {
	d.errback(e)
	return
    }
    d.callback(r)
}

function d_chainErr(d1, d2) {
    d1.addErrback(function (e) {
	d2.errback(e)
    })
}
