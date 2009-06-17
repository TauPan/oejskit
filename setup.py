#
# Copyright (C) Open End AB 2007-2009, All rights reserved
# See LICENSE.txt
#

# assumes setuptools and bdist_egg!

# xxx half-done
from setuptools import setup
import os

version = '0.8.3'

def weblib():
    l = []
    for dirname, dirnames, fnames in os.walk("weblib"):
        l.append((dirname, [os.path.join(dirname, fname) for fname in fnames]))
    return l

setup(
    name="oejskit",
    version=version,
    description='OE Javascript testing and utility kit',
    license='MIT',
    author='Open End AB',
    #author_email=
    #url=    
    py_modules = ['pytest_jstests'],
    packages=['oejskit'],
    zip_safe=False,
    data_files=[
    ('', ['LICENSE.txt']),
    ] + weblib(),
    install_requires=[
        "simplejson"
    ],
    #classifiers=[
    #],
)
