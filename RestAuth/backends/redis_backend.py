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

from django.conf import settings

from backends.base import PropertyBackend
from common.errors import PropertyExists
from common.errors import PropertyNotFound


class RedisPropertyBackend(PropertyBackend):
    """Store properties in a Redis key/value store.

    This backend enables you to store user properties in a key/value store.  Note that the backend
    is not really faster if you only have a few hundred users.

    This backend uses a few additional settings in |file-settings|:

    ``REDIS_HOST``
        The hostname where the redis installation runs.
        Default: ``'localhost'``.
    ``REDIS_PORT``
        The port ot he redis installation. Default: ``6379``.
    ``REDIS_DB``
        The id of the Redis database. Default: ``0``.

    .. NOTE:: Transaction support of this backend is limited. Basic transaction management works,
       but no sensible values are returned for method calls within a transaction.
    """

    library = 'redis'

    _conn = None

    @property
    def conn(self):
        if self._conn is None:
            redis = self._load_library()
            self._conn = redis.StrictRedis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True
            )
        return self._conn

    @property
    def pipe(self):
        if not hasattr(self, '_pipe'):
            self._pipe = self.conn.pipeline()
        return self._pipe

    def list(self, user):
        return self.conn.hgetall(user.id)

    def create(self, user, key, value, dry=False, transaction=True):
        if dry:
            if self.conn.hexists(user.id, key):
                raise PropertyExists(key)
            else:
                return key, value
        else:
            value = self.conn.hsetnx(user.id, key, value)
            if value == 0:
                raise PropertyExists(key)
            else:
                return key, value

    def get(self, user, key):
        value = self.conn.hget(user.id, key)
        if value is None:
            raise PropertyNotFound(key)
        else:
            return value

    def set(self, user, key, value, dry=False, transaction=True):
        old_value = self.conn.hget(user.id, key)

        if not dry:
            self.conn.hset(user.id, key, value)
        return key, old_value

    def set_multiple(self, user, props, dry=False, transaction=True):
        if dry or not props:
            pass  # do nothing
        else:
            self.conn.hmset(user.id, props)

    def init_transaction(self):
        self.conn.execute_command('MULTI')

    def commit_transaction(self):
        self.conn.execute_command('EXEC')

    def rollback_transaction(self):
        self.conn.execute_command('DISCARD')

    def remove(self, user, key):
        value = self.conn.hdel(user.id, key)
        if value == 0:
            raise PropertyNotFound(key)

    def testTearDown(self):
        self.conn.flushdb()
