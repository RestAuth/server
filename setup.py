#!/usr/bin/env python

from distutils.core import setup
import glob

setup(
	name = 'RestAuth',
	author = 'Mathias Ertl',
	author_email = 'mati@fsinf.at',
	url = 'http://fs.fsinf.at/wiki/RestAuth',
	description = 'The RestAuth webservice reference implementation',
	scripts = glob.glob( 'bin/*.py' ),
)

