#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import nested_scopes, generators, with_statement, unicode_literals, absolute_import, division, print_function

import os
from setuptools import setup, find_packages

def read(fname):
	'''open the long description of the project'''
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name='flow',
	version='0.0.9',
	author='Niklas Beuster',
	author_email='niklas.beuster@tu-ilmenau.de',
	description=('Flow based programming with an optional GUI'),
	keywords='flowbased programming gui',
	url='https://makalu3.rz.tu-ilmenau.de/nibe8075/Flow',
	packages=find_packages(),
	include_package_data=True, 
	long_description=read('README.md'),
	install_requires=[],
)
