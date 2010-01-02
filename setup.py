#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#

# assumes setuptools is already installed and bdist_egg!

from setuptools import setup
import os, sys

version = '0.8.7'

def weblib():
    l = []
    for dirname, dirnames, fnames in os.walk("weblib"):
        l.append((dirname, [os.path.join(dirname, fname) for fname in fnames]))
    return l

def long_descr():
    lines = open('doc/doc.txt', 'r').readlines()
    start = []
    for line in lines:
        if 'rest of the docs' in line:
            break
        start.append(line)
    start.append("`rest of the docs... <http://www2.openend.se:/~pedronis/oejskit/doc/doc.html#rest-of-the-docs>`_\n\n")
    start.append("`Europython 2009 talk with examples <http://www2.openend.se:/~pedronis/oejskit/talk>`_\n\n")
    start.append("The project repository lives at http://bitbucket.org/pedronis/js-infrastructure/\n\n")
    start.append("Discussions and feedback should go to py-dev at codespeak.net\n")
    start.append("\nChangelog\n-----------\n")
    start.append(open('CHANGELOG.txt', 'r').read())    
    descr = ''.join(start)
    return descr

def need_simplejson():
    if sys.version_info < (2.6):
        return ["simplejson"]
    return []

setup(
    name="oejskit",
    version=version,
    description='Open End JavaScript testing and utility kit',
    long_description=long_descr(),
    license='MIT',
    author='Open End AB',
    author_email='py-dev@codespeak.net,pedronis@openend.se', # with hpk approval at ep09
    url='http://bitbucket.org/pedronis/js-infrastructure/',
    platforms=['linux', 'osx', 'win32'],
    packages=['oejskit'],
    zip_safe=False,
    include_package_data=True,
    data_files=[
    ('', ['LICENSE.txt', 'CHANGELOG.txt']),
    ] + weblib() + [('doc', ['doc/doc.html', 'doc/style.css'])],
    install_requires=need_simplejson(),
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
    entry_points = {
    'pytest11': ['pytest_jstests = oejskit.pytest_jstests'],
    }
)
