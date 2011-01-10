OE jskit
+++++++++

jskit contains infrastructure and in particular a py.test plugin to
enable running unit tests for JavaScript code inside browsers.
It contains also glue code to run JavaScript tests from unittest.py
based test suites.

The approach also enables to write integration tests such that the
JavaScript code is tested against server-side Python code mocked as
necessary. Any server-side framework that can already be exposed through
WSGI can play.

Known supported browsers are Firefox, Internet Explorer >=7, and
WebKit browsers.

The plugin works with py.test 2.0 or late py.test 1.x.

See CHANGELOG.txt for what's new.

For the documentation see:

doc/doc.html

or online

http://lucediurna.net/oejskit/doc/doc.html

jskit was initially developed by Open End AB and is released under the
MIT license, see LICENSE.txt.
