# -*- encoding: utf-8 -*-
import py
from oejskit.htmlrewrite import (rewrite_html, naive_sanity_check_html,
                               HTMLRewriter, _attrs)


def test_naive_sanity_check_html():
    naive_sanity_check_html("<script src='a'></script>")
    naive_sanity_check_html('<script src="a"></script>')    
    naive_sanity_check_html("<br>")
    naive_sanity_check_html("<br />")
    py.test.raises(ValueError, naive_sanity_check_html, '<script src="a" />')
    py.test.raises(ValueError, naive_sanity_check_html, '<br></br>')
    #py.test.raises(ValueError, naive_sanity_check_html, '<script src="a" >')

class TestHtmlRewrite(object):

    def test_xhtml(self):
        DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'

        html="""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
  <!-- xhtml -->
  <meta http-equiv="content-type" content="text/html; charset=utf-8" />
  <title>Open End Helpdesk</title>
  <link rel="stylesheet" type="text/css" href="/static/en/css/helpdesk.css" />
  <meta name="oe:jsRepos" content="/static /oe-js /lib/mochikit" />
  <script type="text/javascript" src="/oe-js/modular_rt.js"></script>
  <script type="text/javascript" src="/static/en/translation.js"></script>
  <script type="text/javascript" src="/static/boot.js"></script>
  <script type="text/javascript">
  function somefunc() {
  }
  </script>
</head>
<body>
<div>
&nbsp;&#10;åöä
<br />
</div>
</body>
</html>
"""
        html2 = rewrite_html(html)
        assert DOCTYPE in html2
        assert "<!-- xhtml -->" in html2
        assert "<br" in html2
        naive_sanity_check_html(html2)

        expected = html.replace('&#10;', '\n')
        assert html2 == expected

        class TestRewriter(HTMLRewriter):

            def startElement(self, name, attrs):
                if attrs:
                    pairs = []
                    for candName in ('name', 'http-equiv', 'rel', 'type', 'src',
                                     'href', 'content'):
                        if candName in attrs.keys():
                            pairs.append((candName, attrs.getValue(candName)))
                    attrs = _attrs(pairs)
                
                HTMLRewriter.startElement(self, name, attrs)


        html2 = rewrite_html(html, TestRewriter, type='xhtml')
        # xml parsing seems to ignore spaces outside the root element
        # we add manually a newline after the doctype though
        assert html2 == expected.strip()

    def test_html(self):
        DOCTYPE = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
        
        html="""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <!-- html -->
  <meta content="text/html; charset=utf-8" http-equiv="content-type">
  <title>Open End Helpdesk</title>
  <link rel="stylesheet" type="text/css" href="/static/en/css/helpdesk.css">
  <meta name="oe:jsRepos" content="/static /oe-js /lib/mochikit">
  <script type="text/javascript" src="/oe-js/modular_rt.js"></script>
  <script type="text/javascript" src="/static/en/translation.js"></script>
  <script type="text/javascript" src="/static/boot.js"></script>
  <script type="text/javascript">
  function somefunc() {
  }
  </script>
</head>
<body>
<div>
&nbsp;&#10;åöä
<br>
</div>
</body>
</html>
"""
        html2 = rewrite_html(html, type='html')
        assert DOCTYPE in html2
        assert "<!-- html -->" in html2
        assert "<br" in html2
        naive_sanity_check_html(html2)

        expected = html.replace('&#10;', '\n')
        assert html2 == expected
