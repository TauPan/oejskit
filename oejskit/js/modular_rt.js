/*

Copyright (C) OpenEnd 2007-2009, All rights reserved.
See LICENSE.txt

*/


if (typeof(OpenEnd) == "undefined") {
    OpenEnd = {}
}

OpenEnd._GET = function(url, queryString) {
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

OpenEnd.use = function(module) {
// just a marker function
}

OpenEnd.require = function(url) {
// just a marker function
}