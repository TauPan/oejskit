/*

Copyright (C) OpenEnd 2007-2009, All rights reserved.
See LICENSE.txt

*/



TestRunner = {}

InBrowserTesting = {

    poll: function() {
        var self = this
        callLater(0.25, function() {
            // use a post to keep caching issues at bay
            var d = doXHR("/browser_testing/cmd", {method: 'POST'})
            d.addCallback(function(req) {
                var code = evalJSONRequest(req)
                //appendChildNodes('out', P({}, "CODE: [" +code+"]"))
                if (code == "BYE") {
                    self.result({}, 'BYE')
                    return
                }
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

    _waitForPanel: function(label, cb, reload) {
        var n = this.panels[label][0]
        var panel = this.panels[label][1]
        var frame = this.panels[label][2]
        var oldDoc = null
        if (reload) {
            oldDoc = frame.contentWindow.document
        }
        if (frame.readyState != undefined) {
            function check() {
                if (frame.readyState == 'complete' &&
                      frame.contentWindow.document !== oldDoc
                  ) {
                      cb(n, panel, frame, false)
                } else {
                    window.setTimeout(check, 2)
                }
            }
            window.setTimeout(check, 1)
        } else {
            frame.onload = function() {
                frame.onload = null
                cb(n, panel, frame, false)
            }
        }
    },

    doOpen: function(label, url, done) {
        if(label in this.panels) {
            if (done) {
                var info = this.panels[label].concat(true)
                done.apply(null, info)
            }
            return
        }
        var n = this.n;
        this.n += 1;
        var labelNode = P({}, label)
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
        var panel = DIV({"id": "panel-"+n}, labelNode, container, frame)
        var panelsDiv = getElement("panels")
        appendChildNodes(panelsDiv, panel)
        this.panels[label] = [n, panel, frame]
        if (done) {
            this._waitForPanel(label, done)
        }
        frame.src = url
    },

    open: function(url, label) {
        var self = this
        if (label == null) {
            label = url
        }
        self.doOpen(label, url, function (n, panel, frame, reused) {
            self.result({'panel': n}, label);
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
        self.doOpen(url, url, gotTestPage)
    },

    runOneTest: function(url, which, n) {
        var self = this
        var frameWin = this.panels[url][2].contentWindow
        var testing = frameWin.Testing
        testing.runOne(which, function(outcome) {
            self.result(outcome, url+'@'+n)
        })
    },

    'eval': function(label, code, n) {
        var self = this
        var outcome
        var frameWin = this.panels[label][2].contentWindow
        try {
            var result = frameWin.eval(code)
            if (result === undefined) {
                result = null
            }
            outcome = {'result': result}
        } catch (err) {
            s = "FAILED:\n"
            for (var k in err) {
                s +=  k + ": " + err[k] + "\n"
            }
            outcome = {'error': s}
        }
        self.result(outcome, label+'@'+n)        
    },

    travel: function(label, code, n) {
        var self = this
        var frame = this.panels[label][2]

        self._waitForPanel(label, function() {
            self.result({'result': 'reloaded'}, label+'@'+n)
        }, true)

        frame.contentWindow.eval(code)
    }
    
}
