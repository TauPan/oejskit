#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#

# painfully implementing some best-effort rewriting of X/HTML docs
# using what is in the stdlib

# assumes utf-8 right now

import HTMLParser, cStringIO
from xml.sax import saxutils
from xml.sax import handler as saxhandler
import xml.sax.xmlreader
import xml.sax

HTML_EMPTY = ("area", "base", "basefont", "br", "col", "frame", "hr",
              "img", "input", "isindex", "link", "meta", "param")

# meant for sanity checking the output of a rewrite, not more!
def naive_sanity_check_html(html, filename='?'):
    class NaiveSanityHTMLParser(HTMLParser.HTMLParser):
        
        def handle_startendtag(self, tag, attrs):
            if tag in ("div", "script"):
                raise ValueError("%s: start-end %s tags not allowed" %
                                 (self.filename, tag))

        def handle_endtag(self, tag):
            if tag in HTML_EMPTY:
                raise ValueError("%s: end %s tags not expected" %
                                 (self.filename, tag))                
            
    parser = NaiveSanityHTMLParser()
    parser.filename = filename
    parser.feed(html)

class _attrs(object): # minimal attrs impl

    def __init__(self, pairs):
        self.pairs = pairs

    def items(self):
        return self.pairs

class HTMLParsing(HTMLParser.HTMLParser):
    def __init__(self, contentHandler):
        HTMLParser.HTMLParser.__init__(self)
        self.handler = contentHandler

    def handle_starttag(self, tag, attrs):
        self.handler.startElement(tag, _attrs(attrs))

    def handle_endtag(self, tag):
        self.handler.endElement(tag)        

    def handle_data(self, data):
        self.handler.characters(data)

    def handle_charref(self, ref):
        self.handler.characters(unichr(int(ref)))

    def handle_entityref(self, name):
        self.handler.skippedEntity(name)

    def handle_comment(self, data):
        self.handler.comment(data)
        
    def handle_decl(self, decl):
        doctype = decl.lower()
        if doctype.startswith('doctype'):
            if 'xhtml' in doctype:
                self.handler.setType('xhtml')
        self.handler._raw("<!%s>" % decl)

class HTMLRewriter(saxutils.XMLGenerator):
    empty_end = '>'

    def __init__(self, out):
        saxutils.XMLGenerator.__init__(self, out, encoding='utf-8')
        if not hasattr(self, '_write'): # pyxml vs not :(
            self._write = lambda data: self._out.write(data)

    def setType(self, type):
        if type == 'xhtml':
            self.empty_end = ' />'
        else:
            self.empty_end = '>'

    def _raw(self, data):
        self._write(data)

    def emit_chars(self, data):
        saxutils.XMLGenerator.characters(self, data)
    
    def emit_start(self, name, attrs):
        if name in HTML_EMPTY:
            self._write('<' + name)
            for (name, value) in attrs.items():
                self._write(' %s=%s' % (name, saxutils.quoteattr(value)))
            self._write(self.empty_end)
        else:
            saxutils.XMLGenerator.startElement(self, name, attrs)

    def emit_end(self, name):
        if name in HTML_EMPTY:
            return
        saxutils.XMLGenerator.endElement(self, name)

    def rewrite_start(self, name, attrs):
        return False
        
    def startElement(self, name, attrs):
        if not self.rewrite_start(name, attrs):        
            self.emit_start(name, attrs)

    def endElement(self, name):
        self.emit_end(name)

    def characters(self, data):
        self.emit_chars(data)

    def skippedEntity(self, name):
        self._raw('&%s;' % name)

    def startDocument(self):
        pass

    startCDATA = endCDATA = endDTD = lambda self: None

    def comment(self, data):
        self._raw("<!--%s-->" % data)
                
    def startDTD(self, doctype, publicId, systemId):
        # xml parsing seems to ignore spaces outside the root element
        # we add manually a newline after the doctype though
        self._raw('<!DOCTYPE %s PUBLIC "%s" "%s">\n' %
                  (doctype, publicId, systemId))

def rewrite_html(html, Rewriter=HTMLRewriter, type='html',
                 params={}):
    # xxx make encoding an option
    out = cStringIO.StringIO()
    rewriter = Rewriter(out, **params)
    rewriter.setType(type)

    if type == 'xhtml':
        parser = xml.sax.make_parser()
        class EntityResolver(object): #be paranoid
            def resolveEntity(self, publicId, systemId):
                raise RuntimeError("unexpected")
    
        source = xml.sax.xmlreader.InputSource()
        source.setByteStream(cStringIO.StringIO(html))
        source.setEncoding('utf-8')
        parser.setFeature(saxhandler.feature_external_ges, 0)        
        parser.setFeature(saxhandler.feature_external_pes, 0)
        parser.setEntityResolver(EntityResolver())
        parser.setContentHandler(rewriter)
        parser.setProperty(saxhandler.property_lexical_handler, rewriter)
        parser.parse(source)
    else:
        parser = HTMLParsing(rewriter)
        if isinstance(html, str):
            html = html.decode("utf-8")
        parser.feed(html)

    return out.getvalue()
