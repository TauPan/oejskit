#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#

# assumes setuptools is already installed and bdist_egg!

# xxx half-done
from setuptools import setup
import os

version = '0.8.5'

def weblib():
    l = []
    for dirname, dirnames, fnames in os.walk("weblib"):
        l.append((dirname, [os.path.join(dirname, fname) for fname in fnames]))
    return l

setup(
    name="oejskit",
    version=version,
    description='Open End JavaScript testing and utility kit',
    license='MIT',
    author='Open End AB',
    #author_mail=
    url='http://bitbucket.org/pedronis/js-infrastructure/',
    py_modules = ['pytest_jstests'],
    packages=['oejskit'],
    zip_safe=False,
    include_package_data=True,
    data_files=[
    ('', ['LICENSE.txt']),
    ] + weblib() + [('doc', ['doc/doc.html', 'doc/style.css'])],
    install_requires=[
        "simplejson"
    ],
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
)
