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

from __future__ import unicode_literals, absolute_import

from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from common.hashers import import_hash

from backends.base import BackendBase
from backends.base import TransactionManagerBase
from common.errors import PropertyExists
from common.errors import PropertyNotFound
from common.errors import UserExists
from common.errors import UserNotFound


class RedisTransactionManager(TransactionManagerBase):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

_create_user_script = """
local existed = redis.call('hsetnx', KEYS[1], ARGV[1], ARGV[2])
if existed == 0 then
    return {err="UserExists"}
end

redis.call('hset', KEYS[2], ARGV[1], ARGV[3])
"""


class RedisBackend(BackendBase):
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

    def __init__(self, HOST='localhost', PORT=6379, DB=0, **kwargs):
        self.redis = self._load_library()
        kwargs.setdefault('decode_responses', True)
        self.conn = self.redis.StrictRedis(host=HOST, port=PORT, db=DB, **kwargs)
        self._create_user = self.conn.register_script(_create_user_script)

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        password = make_password(password) if password else None
        properties = properties or {}

        if dry is True:  # handle dry mode
            if self.conn.hexists('users', user):
                raise UserExists(user)
            return

        #TODO: handle groups
        self._create_user(keys=['users', 'props'], args=[user, password, properties])

    def list_users(self):
        return self.conn.hkeys('users')

    def user_exists(self, user):
        return self.conn.hexists('users', user)

    def rename_user(self, user, name):
        password = self.conn.hget('users', user)
        if self.conn.hdel('users', user) == 0:
            return UserNotFound(user)
        self.conn.hset('users', name, password)

        properties = self.conn.hget('props', user)
        self.conn.hdel('props', user)
        self.conn.hset('props', name, properties)


    def check_password(self, user, password, groups=None):
        if password is None:
            return False

        def setter(raw_password):
            self.set_password(user, raw_password)

        matches = check_password(password, self.conn.hget('users', user), setter)

        #TODO: handle gruops

        return matches

    def set_password(self, user, password=None):
        password = make_password(password) if password else None
        if self.conn.hexists('users', user):
            self.conn.hset('users', user, password)
        else:
            raise UserNotFound(user)

    def set_password_hash(self, user, algorithm, hash):
        password = import_hash(algorithm, hash)
        if self.conn.hexists('users', user):
            self.conn.hset('users', user, password)
        else:
            raise UserNotFound(user)

    def remove_user(self, user):
        if self.conn.hdel('users', user) == 0:
            raise UserNotFound(user)
        self.conn.hdel('props', user)

        #TODO: handle gruops

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

    def remove(self, user, key):
        value = self.conn.hdel(user.id, key)
        if value == 0:
            raise PropertyNotFound(key)

    def testSetUp(self):
        self.conn.flushdb()

    def testTearDown(self):
        self.conn.flushdb()
