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

import random

from django.conf import settings


class MasterSlave(object):
    """This router assumes that you have a single master (that can perform write operations) and
    multiple slaves that perform read operations.

    Read operations will be redirected to a random database (including the master) and write
    operations will be directed to the "default" database, which should be the master.
    """
    def db_for_read(self, model, **hints):
        choices = settings.DATABASES.keys()
        return random.choice(choices)


class MultipleMasterSlave(object):
    """This router handles multiple (read/write) masters and (read-only) slaves.

    Read operations will be redirected to a random database (including any masters).
    Write-operations will be redirected to a random database with a designation starting with
    'master'.

    Example:

    .. code-block:: python

       DATABASES = {
            'master-a': { ... }, # will get write operations
            'master-b': { ... }, # will get write operations
            'slave': { ... }, # this is a read-only slave
       }

    """
    def db_for_read(self, model, **hints):
        choices = settings.DATABASES.keys()
        return random.choice(choices)

    def db_for_write(self, model, **hints):
        databases = settings.DATABASES.keys()
        choices = [db for db in databases if db.startswith('master')]
        return random.choice(choices)
