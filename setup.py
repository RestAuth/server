#!/usr/bin/env python
#
# This file is part of RestAuth (http://fs.fsinf.at/wiki/RestAuth).
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RestAuth.  If not, see <http://www.gnu.org/licenses/>.

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

