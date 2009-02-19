try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
version = '0.9'

setup(
    name="oejskit",
    version=version,
    description='OE Javascript testing and utility kit',
    #license='MIT', ?
    author='Open End AB',
    #author_email=
    #url=    
    packages=['oejskit'],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "simplejson"
    ],
    #classifiers=[
    #],
)
