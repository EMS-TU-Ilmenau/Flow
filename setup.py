#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import nested_scopes, generators, with_statement, unicode_literals, absolute_import, division, print_function

import os
from setuptools import setup

def read(fname):
	'''open the long description of the project'''
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name='satcomdevctrl',
	version='0.1',
	author='Niklas Beuster',
	author_email='beustens@iis.fraunhofer.de',
	description=('Device classes to communicate with several devices located at the FORTE lab in Ilmenau'),
	license='Fraunhofer IIS/DVT',
	keywords='device measurements satcom',
	url='https://git01.iis.fhg.de/dvt-forte/SatcomDevCtrl',
	packages=['satcomdevctrl', 'satcomdevctrl.interfaces'],
	long_description=read('README.md'),
	install_requires=['pyvisa-py', 'pyserial>=3.0'],
	classifiers=[
		'Development Status :: 1 - Alpha',
		'Topic :: Utilities',
		'License :: Fraunhofer :: proprietary',
	],
)
