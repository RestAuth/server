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

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.utils import six

from backends.base import BackendBase
from backends.base import TransactionManagerBase
from common.hashers import import_hash
from common.errors import GroupExists
from common.errors import GroupNotFound
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

if #ARGV >= 3 then
    redis.call('hmset', KEYS[2], unpack(ARGV, 3))
end
"""

_rename_user_script = """
-- get old user
local hash = redis.call('hget', KEYS[1], ARGV[1])
if not hash then
    return {err="UserNotFound"}
end
if redis.call('hexists', KEYS[1], ARGV[2]) == 1 then
    return {err="UserExists"}
end

-- delete old user
redis.call('hdel', KEYS[1], ARGV[1])

-- set new username
redis.call('hset', KEYS[1], ARGV[2], hash)

-- rename properties
local props = redis.call('hget', KEYS[2], ARGV[1])
redis.call('hdel', KEYS[2], ARGV[1])
redis.call('hset', KEYS[2], ARGV[2], props)"""

_create_property_script = """
if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end
if redis.call('hexists', KEYS[2], ARGV[2]) == 1 then
    return {err="PropertyExists"}
end
redis.call('hset', KEYS[2], ARGV[2], ARGV[3])"""

_set_property_script = """
if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end

local old = redis.call('hget', KEYS[2], ARGV[2])
redis.call('hset', KEYS[2], ARGV[2], ARGV[3])
return old
"""

_set_properties_script = """
if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end

redis.call('hmset', KEYS[2], unpack(ARGV, 2))"""

_remove_property_script = """
if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end
if redis.call('hexists', KEYS[2], ARGV[2]) == 0 then
    return {err="PropertyNotFound"}
end
redis.call('hdel', KEYS[2], ARGV[2])
"""

#keys = [g_key, sg_key, self._sg_key(group, service),
#        self._mg_key(subgroup, subservice), ]
#args = [group, subgroup, self._gu_key(group, service),
#        self._gu_key(subgroup, subservice), ]
#self._add_subgroup(keys=keys, args=args)
_add_subgroup_script = """
-- check if groups exist
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err=KEYS[1]}
elseif redis.call('sismember', KEYS[2], ARGV[2]) == 0 then
    return {err=KEYS[2]}
end

-- add relation
redis.call('sadd', KEYS[3], ARGV[4])
redis.call('sadd', KEYS[4], ARGV[3])
"""

# g_key = self._g_key(service)
# sg_keys = [self._g_key(subservice) for g in subgroups]  # because thi will be a tuple
# gu_keys = [self._gu_key(g, subservice) for g in subgroups]
#
# keys = [sg_key, g_key, ] + sg_keys
# args = [group, ] + subgroups + gu_keys
# self._set_subgroups(keys=keys, args=args)
_set_subgroups_script = """
for i=2, #KEYS, 1 do
    if redis.call('sismember', KEYS[i], ARGV[i - 1]) == 0 then
        return {err=KEYS[i] .. "_" .. ARGV[i - 1]}
    end
end

for i=#KEYS - 1, #ARGS 1 do
    redis.call('sadd', KEYS[1], ARGV[i])
end
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

        # register scripts
        self._create_user = self.conn.register_script(_create_user_script)
        self._rename_user = self.conn.register_script(_rename_user_script)
        self._create_property = self.conn.register_script(_create_property_script)
        self._set_property = self.conn.register_script(_set_property_script)
        self._set_properties = self.conn.register_script(_set_properties_script)
        self._remove_property = self.conn.register_script(_remove_property_script)
        self._add_subgroup = self.conn.register_script(_add_subgroup_script)


    def _listify(self, d):
        l = []
        [l.extend(t) for t in six.iteritems(d)]
        return l

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        password = make_password(password) if password else ''
        properties = properties or {}

        if dry is True:  # handle dry mode
            if self.conn.hexists('users', user):  # this is really the only error condition
                raise UserExists(user)
            return

        try:
            # TODO: handle groups
            return self._create_user(keys=['users', 'props_%s' % user],
                                     args=[user, password, ] + self._listify(properties))
        except self.redis.ResponseError as e:
            if e.message == 'UserExists':
                raise UserExists(user)
            raise

    def list_users(self):
        return self.conn.hkeys('users')

    def user_exists(self, user):
        return self.conn.hexists('users', user)

    def rename_user(self, user, name):
        try:
            # TODO: handle gruops
            self._rename_user(keys=['users', 'props'], args=[user, name])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            elif e.message == 'UserExists':
                raise UserExists(name)
            raise

    def check_password(self, user, password, groups=None):
        if password is None:
            return False

        def setter(raw_password):
            self.set_password(user, raw_password)

        stored = self.conn.hget('users', user)
        if stored is None:
            raise UserNotFound(user)
        matches = check_password(password, stored, setter)

        # TODO: handle gruops

        return matches

    def set_password(self, user, password=None):
        # TODO: rewrite as lua script
        password = make_password(password) if password else None
        if self.conn.hexists('users', user):
            self.conn.hset('users', user, password)
        else:
            raise UserNotFound(user)

    def set_password_hash(self, user, algorithm, hash):
        # TODO: rewrite as lua script
        password = import_hash(algorithm, hash)
        if self.conn.hexists('users', user):
            self.conn.hset('users', user, password)
        else:
            raise UserNotFound(user)

    def remove_user(self, user):
        # TODO: rewrite as lua script
        if self.conn.hdel('users', user) == 0:
            raise UserNotFound(user)
        self.conn.hdel('props', user)
        # TODO: handle groups

    def list_properties(self, user):
        # TODO: this method should be called 'get_properties', since we don't return a list.

        pipe = self.conn.pipeline()
        pipe.hexists('users', user)
        pipe.hgetall('props_%s' % user)
        exists, properties = pipe.execute()
        if exists is False:
            raise UserNotFound(user)
        return properties

    def create_property(self, user, key, value, dry=False):
        if dry is True:  # shortcut, can be done with simple pipe
            pipe = self.conn.pipeline()
            pipe.hexists('users', user)
            pipe.hexists('props_%s' % user)
            user_exists, prop_exists = pipe.execute()
            if user_exists is False:
                raise UserNotFound(user)
            elif prop_exists is True:
                raise PropertyExists(key)

        try:
            self._create_property(keys=['users', 'props_%s' % user], args=[user, key, value])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            elif e.message == 'PropertyExists':
                raise PropertyExists(key)
            raise

    def get_property(self, user, key):
        pipe = self.conn.pipeline()
        pipe.hexists('users', user)
        pipe.hget('props_%s' % user, key)
        exists, value = pipe.execute()
        if not exists:
            raise UserNotFound(user)
        elif value is None:
            raise PropertyNotFound(key)
        return value

    def set_property(self, user, key, value):
        try:
            return self._set_property(keys=['users', 'props_%s' % user], args=[user, key, value])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

    def set_properties(self, user, properties):
        if not properties:
            if not self.conn.hexists('users', user):
                raise UserNotFound(user)
            return

        try:
            self._set_properties(keys=['users', 'props_%s' % user],
                                 args=[user, ] + self._listify(properties))
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

    def remove_property(self, user, key):
        try:
            self._remove_property(keys=['users', 'props_%s' % user], args=[user, key])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            if e.message == 'PropertyNotFound':
                raise PropertyNotFound(key)
            raise

    # groups_<service.id> == set of groups for a service
    def _g_key(self, service):
        return 'groups_%s' % service.id if service is not None else 'None'

    # members_<service.id>_<group> == set of users in a group
    def _gu_key(self, group, service):
        return 'members_%s_%s' % (service.id if service is not None else 'None', group)

    # index of subgroups:
    def _sg_key(self, group, service):
        return 'subgroups_%s_%s' % (service.id if service is not None else 'None', group)

    # index of metagroups:
    def _mg_key(self, group, service):
        return 'metagroups_%s_%s' % (service.id if service is not None else 'None', group)

    def _parse_key(self, key):
        _, sid, name = key.split('_')
        if sid == 'None':
            return (name, None)
        else:
            return (name, int(sid))

    def list_groups(self, service, user=None):
        if user is None:
            return list(self.conn.smembers(self._g_key(service)))
        else:
            pass  # TODO

    def create_group(self, group, service, users=None, dry=False):
        # TODO: rewrite as lua script

        g_key = self._g_key(service)
        if self.conn.sismember(g_key, group):
            raise GroupExists(group, service)
        elif dry is True:
            return

        self.conn.sadd(g_key, group)

        # add users
        if users is not None:
            # multi value insert in lua - use unpack:
            # http://redis.io/commands/sadd#comment-800126580
            self.conn.sadd(self.gu_key(group, service), *users)

    def rename_group(self, group, name, service):
        # TODO: rename self._g_key, self._gu_key
        pass

    def set_group_service(self, group, service, new_service):
        # TODO: rename self._g_key, self._gu_key
        pass

    def group_exists(self, group, service):
        return self.conn.sismember(self._g_key(service), group)

    def set_memberships(self, user, service, groups):
        pass  # TODO

    def set_members(self, group, service, users):
        # TODO: rewrite as lua script
        if self.conn.sismember(self._g_key(service), group) is False:
            raise GroupNotFound(group, service)

        gu_key = self._gu_key(group, service)

        self.conn.delete(gu_key)  # clear set
        self.conn.sadd(gu_key, *users)

    def add_member(self, group, service, user):
        # TODO: rewrite as lua script
        if self.conn.sismember(self._g_key(service), group) is False:
            raise GroupNotFound(group, service)

        self.conn.sadd(self._gu_key(group, service), user)

    def members(self, group, service, depth=None):
        if depth is None:
            depth = settings.GROUP_RECURSION_DEPTH

        if depth == 0:  # shortcut for now
            return list(self.conn.smembers(self._gu_key(group, service)))

    def is_member(self, group, service, user):
        # 1. get list of meta-groups
        # 2. do an intersection
        pass  # TODO

    def remove_member(self, group, service, user):
        # TODO: rewrite as lua script
        pass  # TODO

    def add_subgroup(self, group, service, subgroup, subservice):
        g_key = self._g_key(service)
        sg_key = self._g_key(subservice)

        keys = [g_key, sg_key, self._sg_key(group, service), self._mg_key(subgroup, subservice)]
        args = [group, subgroup, self._gu_key(group, service), self._gu_key(subgroup, subservice)]
        try:
            self._add_subgroup(keys=keys, args=args)
        except self.redis.ResponseError as e:
            # TODO: g_key/sg_key not adequate, should include groupname
            if e.message == g_key:
                raise GroupNotFound(group, service)
            elif e.message == sg_key:
                raise GroupNotFound(subgroup, subservice)
            raise

    def set_subgroups(self, group, service, subgroups, subservice):
        # TODO: subgroups should be a list of tuples with service
        g_key = self._g_key(service)
        sg_keys = [self._g_key(subservice) for g in subgroups]  # because thi will be a tuple
        gu_keys = [self._gu_key(g, subservice) for g in subgroups]

        keys = [g_key, ] + sg_keys
        args = [group, ] + subgroups + gu_keys
        try:
            self._set_subgroups(keys=keys, args=args)
        except self.redis.ResponseError as e:
            raise GroupNotFound(*self._parse_key(e.message))

    def is_subgroup(self, group, service, subgroup, subservice):
        return self.conn.sismember(self._sg_key(group, service),
                                   self._gu_key(subgroup, subservice))

    def subgroups(self, group, service, filter=True):
        return [self._parse_key(k) for k in self.conn.smembers(self._sg_key(group, service))]

    def parents(self, group, service):
        return [self._parse_key(k) for k in self.conn.smembers(self._mg_key(group, service))]

    def remove_subgroup(self, group, service, subgroup, subservice):
        # TODO: rewrite as lua script
        # TODO: no checking of group existance yet
        return self.conn.srem(self._sg_key(group, service), self._gu_key(subgroup, subservice))

    def testSetUp(self):
        self.conn.flushdb()

    def testTearDown(self):
        self.conn.flushdb()
