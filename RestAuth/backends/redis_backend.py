# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RestAuth.  If not, see <http://www.gnu.org/licenses/>.

import redis

from django.conf import settings

from RestAuth.common.errors import PropertyExists, PropertyNotFound

conn = redis.StrictRedis(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
    db=getattr(settings, 'REDIS_DB', 0),
    decode_responses=True
)


class RedisPropertyBackend(object):
    """Store properties in a Redis key/value store.

    This backend enables you to store user properties in a key/value store.
    Note that the backend is not really faster if you only have a few hundred
    users.

    This backend uses a few additional settings:

    ``REDIS_HOST``
        The hostname where the redis installation runs.
        Default: ``'localhsot'``.
    ``REDIS_PORT``
        The port ot he redis installation. Default: ``6379``.
    ``REDIS_DB``
        The id of the Redis database. Default: ``0``.
    """
    def list(self, user):
        return conn.hgetall(user.id)

    def create(self, user, key, value, dry=False):
        if dry:
            if conn.hexists(user.id, key):
                raise PropertyExists(key)
            else:
                return key, value
        else:
            value = conn.hsetnx(user.id, key, value)
            if value == 0:
                raise PropertyExists(key)
            else:
                return key, value

    def get(self, user, key):
        value = conn.hget(user.id, key)
        if value is None:
            raise PropertyNotFound(key)
        else:
            return value

    def set(self, user, key, value):
        old_value = conn.hget(user.id, key)
        conn.hset(user.id, key, value)
        return key, old_value

    def set_multiple(self, user, props, dry=False):
        if dry or not props:
            pass  # do nothing
        else:
            conn.hmset(user.id, props)

    def remove(self, user, key):
        value = conn.hdel(user.id, key)
        if value == 0:
            raise PropertyNotFound(key)

    def testTearDown(self):
        conn.flushdb()
