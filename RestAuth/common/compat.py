# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

"""Code to handle Python version incompatibilities."""

from __future__ import unicode_literals

from django.utils import six


def encode_str(s):
    """Encode a string so its safe to pass to tests of cli-scripts."""
    return s if six.PY3 else s.encode('utf-8')


def decode_str(s):
    """Decode a string so its safe to output in cli-scripts."""
    return s if six.PY3 else s.decode('utf-8')
