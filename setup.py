#!/usr/bin/env python

# -*- coding: utf-8 -*-

import os
import sys

import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Backwards compatibility for Python 2.x
try:
    from itertools import ifilter
    filter = ifilter
except ImportError:
    pass


def get_version():
    '''
    Version slurping without importing stackslurp, since dependencies may not be
    met until setup is run.
    '''
    version_regex = re.compile(r"__version__\s+=\s+"
                               r"['\"](\d+.\d+.\d+\w*)['\"]$")
    versions = filter(version_regex.match, open("stackslurp/__init__.py"))

    try:
        version = next(versions)
    except StopIteration:
        raise Exception("stackslurp version not set")

    return version_regex.match(version).group(1)

version = get_version()

# Utility for publishing stackslurp, courtesy kennethreitz/requests
if sys.argv[-1] == 'publish':
    print("Publishing stackslurp {version}".format(version=version))
    os.system('python setup.py sdist upload')
    sys.exit()

packages = ['stackslurp']
requires = []

with open('requirements.txt') as reqs:
    requires = reqs.read().splitlines()

setup(name='stackslurp',
      version=version,
      description='Grab recent questions on StackExchange, send to a CloudQueue',
      long_description=open('README.md').read(), # Switch to generated RST later.
      author='Kyle Kelley',
      author_email='kyle.kelley@rackspace.com',
      url='',
      packages=packages,
      package_data={'': ['LICENSE']},
      include_package_data=False,
      install_requires=requires,
      entry_points={
          'console_scripts': [
              'slurp = stackslurp.main:main',
          ]
      },
      # license=open('LICENSE').read(),
      zip_safe=False,
      classifiers=(
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Environment :: OpenStack',
          'License :: OSI Approved :: Apache Software License',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
      ),
)
