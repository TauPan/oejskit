/*

Copyright (C) OpenEnd 2007, All rights reserved

Reviewed: 

*/

TestRunner = {}

InBrowserTesting = {

    poll: function() {
	var self = this
	callLater(0.25, function() {
	    var d = loadJSONDoc("/browser_testing/cmd")
	    d.addCallback(function(code) {
		self.poll()
		if (code == null) {
		    return
		}
		eval(code)
	    })
	})
    },

    n: 0,

    panels: {},

    result: function(data, discrim) {
	var xhr = getXMLHttpRequest()
	xhr.open('POST', "/browser_testing/result")
	xhr.setRequestHeader('Content-Type', 'text/json')
        if(!discrim) {
	    discrim = null
        }
	xhr.send(serializeJSON({discrim: discrim, res: data}))
    },

    nprepared: 0,
    first_name: null,

    prepare: function(name) {
        var n  = this.nprepared
        this.nprepared++
	var panelsDiv = getElement("panels")
        if (n == 0) {
            document.title = name
            this.first_name = name
        } else {
            document.title = this.first_name+" ... "+name
            appendChildNodes(panelsDiv, HR())
        }

        appendChildNodes(panelsDiv, H1({}, name))
	this.result('prepared', 'prepared:'+name)
    },

    doOpen: function(url, done) {	
        if(url in this.panels) {
	    if (done) {
		var info = this.panels[url].concat(true)
		done.apply(null, info)
            }
	    return
        }
	var n = this.n;
        this.n += 1;
        var label = H2({}, url)
	var frame = createDOM('IFRAME', {"id": "panel-frame-"+n, 
		                         "width": "70%", "height": "100px" })
        var expand = BUTTON("Expand")
        expand.onclick=function(event) { 
            var doc = frame.contentWindow.document
            var height = doc.documentElement.offsetHeight
            var scrollHeight = doc.body.scrollHeight
            if (scrollHeight > height) {
                height = scrollHeight
            }
            frame.height = height
        }
        var contract = BUTTON("Contract")
        contract.onclick=function(event) { frame.height = frame.height / 2 }
        var container = DIV({"style": "display: block"}, contract, expand)
        var panel = DIV({"id": "panel-"+n}, label, container, frame)
	var panelsDiv = getElement("panels")
	appendChildNodes(panelsDiv, panel)
	this.panels[url] = [n, panel, frame]
	if (done) {
	    if (frame.readyState != undefined) {
		function check() {
		    if (frame.readyState == 'complete') {
			done(n, panel, frame, false)
		    } else {
			window.setTimeout(check, 2)
		    }
		}
		window.setTimeout(check, 1)
	    } else {
		frame.onload = function() {
		    done(n, panel, frame, false)
		}
            }
	}
	frame.src = url
    },

    open: function(url) {
	var self = this
	self.doOpen(url, function (n, panel, frame, reused) {
	    self.result({'panel': n}, url);
	})
    },

    collectTests: function(url) {
	var self = this
	function gotTestPage(n, panel, frame, reused) {
	    var frameWin = frame.contentWindow
	    var testing = frameWin.Testing
	    var collected = []
	    if (testing) {
		collected = testing.collect()
            }
	    self.result(collected, url+'@collect')
        }
	self.doOpen(url, gotTestPage)
    },

    runOneTest: function(url, which, n) {
	var self = this
        var frameWin = this.panels[url][2].contentWindow
	var testing = frameWin.Testing
	testing.runOne(which, function(outcome) {
	    self.result(outcome, url+'@'+n)
	})
    },

    'eval': function(url, code, n) {
	var self = this
	var outcome
        var frameWin = this.panels[url][2].contentWindow
	try {
	    var result = frameWin.eval(code)
	    outcome = {'result': result}
	} catch (err) {
	    s = "FAILED:\n"
            for (var k in err) {
		s +=  k + ": " + err[k] + "\n"
            }
	    outcome = {'error': s}
        }
	self.result(outcome, url+'@'+n)	
    }
    
}
