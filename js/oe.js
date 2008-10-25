/*
 Copyright (C) Open End AB 2007, All rights reserved
*/

if (typeof(OE) == "undefined") {
    OE = { _path: [], _loadedScripts: {} }
}

OE._GET = function(url, queryString) {
    var xreq;
    if (XMLHttpRequest != undefined) {
        xreq = new XMLHttpRequest();
    } else {
        xreq = new ActiveXObject("Microsoft.XMLHTTP");
    }

    if (queryString) {
	url = url + '?' +queryString
    }

    xreq.open("GET", url, false);
    try {
        xreq.send(null);
        if (xreq.status == 200 || xreq.status == 0)
            return xreq.responseText;
    } catch (e) {
        return null;
    };
    return null;    
}

OE._findDeps = function (module, repos)  {
    var repos = repos.join(':')
    var res = OE._GET("/_jsDeps", "module=" + module + "&repos=" + repos)
    if (!res) {
	return []
    }
    res = eval("(" + res + ")")
    return res
}

OE.addRepository = function() {
    var els = arguments;
    for (var i = els.length - 1; i>=0; i--) {
        OE._path.unshift(els[i])
    }

}

OE._injectDeps = function(deps) {
    for (var i=0; i<deps.length; i++) {
	var dep = deps[i]
	if (!(dep in OE._loadedScripts)) {
	    OE._loadedScripts[dep] = null
	    document.writeln('<script type="text/javascript" src="'+dep+'"></script>')
        }
    }
}

OE.topUse = function(module) {
    var deps = OE._findDeps(module, OE._path)
    OE._injectDeps(deps)
}

OE.topScript = function(url) {
    var deps = OE._findDeps(url, OE._path)
    OE._injectDeps(deps)
}

OE.use = function(module) {
// just a marker function
}

OE.require = function(url) {
// just a marker function
}