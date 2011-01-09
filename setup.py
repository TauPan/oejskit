#
# Copyright (C) Open End AB 2007-2011, All rights reserved
# See LICENSE.txt
#

# assumes setuptools is already installed and bdist_egg!

from setuptools import setup
import os, sys


version = '0.9.0'

BRIDGE = """
`rest of the docs... <http://lucediurna.net/oejskit/doc/doc.html#rest-of-the-docs>`_

`Europython 2009 talk with examples <http://lucediurna.net/oejskit/talk>`_

The project repository lives at http://bitbucket.org/pedronis/js-infrastructure/

Discussions and feedback should go to py-dev at codespeak.net

Changelog
-----------
"""


def long_descr():
    lines = open('doc/doc.txt', 'r').readlines()
    start = []
    for line in lines:
        if 'rest of the docs' in line:
            break
        start.append(line)
    start.append(BRIDGE.lstrip())
    start.append(open('CHANGELOG.txt', 'r').read())
    descr = ''.join(start)
    return descr


setup(
    name="oejskit",
    version=version,
    description='Open End JavaScript testing and utility kit',
    long_description=long_descr(),
    license='MIT',
    author='Open End AB',
    # with hpk approval at ep09
    author_email='py-dev@codespeak.net,pedronis@openend.se',
    url='http://bitbucket.org/pedronis/js-infrastructure/',
    platforms=['linux', 'osx', 'win32'],
    packages=['oejskit'],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: POSIX',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: MacOS :: MacOS X',
    'Topic :: Software Development :: Testing',
    'Topic :: Software Development :: Quality Assurance',
    'Topic :: Utilities',
    'Programming Language :: Python',
    'Programming Language :: JavaScript'
    ],
    entry_points={
    'pytest11': ['pytest_jstests = oejskit.pytest_jstests'],
    }
)
