/*

Copyright (C) OpenEnd 2007-2010, All rights reserved.
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
                if (typeof(code) == "string") {
                    eval(code)
                } else {
                    var op = code['op']
                    var args = code['args']
                    var name = code['name'] || "whatever"
                    self[op].apply(self, [name].concat(args))
                }
            })
        })
    },

    result: function(data, discrim) {
        var xhr = getXMLHttpRequest()
        xhr.open('POST', "/browser_testing/result")
        xhr.setRequestHeader('Content-Type', 'text/json')
        if(!discrim) {
            discrim = null
        }
        xhr.send(serializeJSON({discrim: discrim, res: data}))
    },

    n: 0,
    panels: {},
    sections: {},

    ensure: function(name) {
        document.title = name
        if (name in this.sections) {
            return this.sections[name]
        }
        var panelsDiv = getElement("panels")
        var title = H1({}, name)
        var anchor = A({name: name})
        var hr = HR()
        var delims = [title, anchor, hr]
        this.sections[name] = delims
        appendChildNodes(panelsDiv, delims)
        var UR = getElement("UR")
        appendChildNodes(UR, P({}, A({href: "#"+name}, name)))
        return delims
    },

    prepare: function(name) {
        this.ensure(name)
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

    doOpen: function(name, label, url, done) {
        delims = this.ensure(name)
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
        var bottom = delims[2]
        insertSiblingNodesBefore(bottom, panel)
        this.panels[label] = [n, panel, frame]
        if (done) {
            this._waitForPanel(label, done)
        }
        frame.src = url
    },

    open: function(name, url, label) {
        var self = this
        if (label == null) {
            label = url
        }
        self.doOpen(name, label, url, function (n, panel, frame, reused) {
            self.result({'panel': n}, label);
        })
    },

    collectTests: function(name, url) {
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
        self.doOpen(name, url, url, gotTestPage)
    },

    runOneTest: function(name, url, which, n) {
        var self = this
        this.ensure(name)
        var frameWin = this.panels[url][2].contentWindow
        var testing = frameWin.Testing
        testing.runOne(which, function(outcome) {
            self.result(outcome, url+'@'+n)
        })
    },

    'eval': function(name, label, code, n) {
        var self = this
        this.ensure(name)
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

    travel: function(name, label, code, n) {
        var self = this
        this.ensure(name)
        var frame = this.panels[label][2]

        self._waitForPanel(label, function() {
            self.result({'result': 'reloaded'}, label+'@'+n)
        }, true)

        frame.contentWindow.eval(code)
    }

}
