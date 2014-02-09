# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


def import_path(path):
    try:
        modname, attrname = path.rsplit('.', 1)
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t a middleware module' % path)

    try:
        mod = import_module(modname)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' % (modname, e))
    try:
        return getattr(mod, attrname), attrname
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" class'
        raise ImproperlyConfigured(msg % (modname, attrname))
