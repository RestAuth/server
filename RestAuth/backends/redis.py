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

from Services.models import Service
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
    # we don't really support transactions ATM

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

# keys=['users', 'props_%s' % user] + list(group_keys)
# args=[user, password, len(properties)] + properties + groups
_create_user_script = """
if redis.call('hsetnx', KEYS[1], ARGV[1], ARGV[2]) == 0 then
    return {err="UserExists"}
end

local last_prop = tonumber(ARGV[3])

if #ARGV >= 4 and last_prop > 3 then -- last_prop == 3 -> no properties
    redis.call('hmset', KEYS[2], unpack(ARGV, 4, last_prop))
end

for i=1 + last_prop, #ARGV, 2 do
    redis.call('sadd', "groups_" .. ARGV[i], ARGV[i+1])
    redis.call('sadd', "members_" .. ARGV[i] .. "_" .. ARGV[i+1], ARGV[1])
end
"""

# keys=['users'], args=[user, password]
_set_password_script = """
if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end
redis.call('hset', KEYS[1], ARGV[1], ARGV[2])
"""

# keys = ['users', 'props_%s' % user, 'props_%s' % name]
# args = [user, name]
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
redis.call('rename', KEYS[2], KEYS[3])"""

# keys = ['users', 'props_%s' % user] + [members_*]
# args = [user]
_remove_user_script = """
if redis.call('hdel', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end

redis.call('del', KEYS[2])
for i=3, #KEYS, 1 do
    p.call('srem', KEY[i], ARGV[1])
end
"""

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
elseif redis.call('hexists', KEYS[2], ARGV[2]) == 0 then
    return {err="PropertyNotFound"}
end
redis.call('hdel', KEYS[2], ARGV[2])
"""

# keys = [g_key, old_gu_key, new_gu_key, old_sg_key, new_sg_key] + mg_keys
# args = [group, name, sid]
_rename_group_script = """
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err="GroupNotFound"}
elseif redis.call('sismember', KEYS[1], ARGV[2]) == 1 then
    return {err="GroupExists"}
end

-- rename grouop
redis.call('srem', KEYS[1], ARGV[1])
redis.call('sadd', KEYS[1], ARGV[2])

-- rename user keys
if redis.call('exists', KEYS[2]) == 1 then
    redis.call('rename', KEYS[2], KEYS[3])
end
-- rename subgroup key
if redis.call('exists', KEYS[4]) == 1 then
    redis.call('rename', KEYS[4], KEYS[5])
end

-- rename meta-group keys
local old_ref = ARGV[3] .. '_' .. ARGV[1]
local new_ref = ARGV[3] .. '_' .. ARGV[2]
for i=6, #KEYS, 1 do
    redis.call('srem', KEYS[i], old_ref)
    redis.call('sadd', KEYS[i], new_ref)
end
"""

# keys = [old_g_key, new_g_key, old_gu_key, new_gu_key, old_sg_key, new_sg_key] + mg_keys
# args = [group, old_sid, new_sid]
_set_service_script = """
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err="GroupNotFound"}
elseif redis.call('sismember', KEYS[2], ARGV[1]) == 1 then
    return {err="GroupExists"}
end

-- rename grouop
redis.call('srem', KEYS[1], ARGV[1])
redis.call('sadd', KEYS[2], ARGV[1])

-- rename user keys
if redis.call('exists', KEYS[3]) == 1 then
    redis.call('rename', KEYS[3], KEYS[4])
end
-- rename subgroup key
if redis.call('exists', KEYS[5]) == 1 then
    redis.call('rename', KEYS[5], KEYS[6])
end

-- rename meta-group keys
local old_ref = ARGV[2] .. '_' .. ARGV[1]
local new_ref = ARGV[3] .. '_' .. ARGV[1]
for i=7, #KEYS, 1 do
    redis.call('srem', KEYS[i], old_ref)
    redis.call('sadd', KEYS[i], new_ref)
end
"""

# keys = ['users', g_key] + [self._gu_key(g, service) for g in self.conn.smembers(g_key)]
# args = [user, service] + groups
_set_memberships_script = """
if redis.call('hexists', KEYS[1], ARGV[1]) == 0 then
    return {err="UserNotFound"}
end

-- remove existing memberships
for i=3, #KEYS, 1 do
    -- TODO: Skip keys present in ARGV[3:]?
    redis.call('srem', KEYS[i], ARGV[1])
end

-- create any groups that don't exist yet
if #ARGV > 2 then
    redis.call('sadd', KEYS[2], unpack(ARGV, 3))
end

-- add user to groups
for i=3, #ARGV, 1 do
    redis.call('sadd', 'members_' .. ARGV[2] .. '_' .. ARGV[i], ARGV[1])
end
"""

# keys=[self._g_key(service), 'user', self._gu_key(group, service)]
# args=[group, user])
_add_member_script = """
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err="GroupNotFound"}
elseif redis.call('hexists', KEYS[2], ARGV[2]) == 0 then
    return {err="UserNotFound"}
end
redis.call('sadd', KEYS[3], ARGV[2])
"""

# keys=[self._g_key(service), self._gu_key(group, service)]
# args=[group, user])
_remove_member_script = """
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err="GroupNotFound"}
elseif redis.call('srem', KEYS[2], ARGV[2]) == 0 then
    return {err="UserNotFound"}
end
"""

# keys = [g_key, sg_key, self._sg_key(group, service), self._mg_key(subgroup, subservice)]
# args = [group, subgroup, self._ref_key(group, service), self._ref_key(subgroup, subservice)]
_add_subgroup_script = """
-- check if groups exist
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err=ARGV[3]}
elseif redis.call('sismember', KEYS[2], ARGV[2]) == 0 then
    return {err=ARGV[4]}
end

-- add relation
redis.call('sadd', KEYS[3], ARGV[4])
redis.call('sadd', KEYS[4], ARGV[3])
"""

# sg_key = self._sg_key(group, service)  # stores subgroups
# g_key = self._g_key(service)  # test for existance here
# sid = self._sid(service)  # used for reference
# g_keys = [self._g_key(subservice) for g in subgroups]  # test for existance here
# ref_keys = [self._ref_key(g, subservice) for g in subgroups]  # used for reference
# mg_keys = [self._mg_key(g, subservice) for g in subgroups]  # stores metagroup
# add_mg_keys = ['metagroups_%s' % k for k in self.conn.smembers(sg_key)]
#
# keys = [sg_key, g_key, ] + g_keys + mg_keys + [k for k in add_mg_keys if k not in mg_keys]
# args = [sid, group, ] + subgroups + ref_keys
_set_subgroups_script = """
local no_groups = (#ARGV - 2) / 2
local group_ref = ARGV[1] .. '_' .. ARGV[2]

-- Verify that all groups exist
for i=2, no_groups + 2, 1 do
    if redis.call('sismember', KEYS[i], ARGV[i]) == 0 then
        return {err=ARGV[i]}
    end
end

-- Remove subgroup relations.
-- This is a poor-(wo)mans sscan, because it is not allowed in LUA scripts
local subgroups = redis.call('smembers', KEYS[1])
local to_remove = {}
for i=1, #subgroups, 1 do
    if string.match(subgroups[i], ARGV[1] .. '_') ~= nil then
        to_remove[#to_remove+1] = subgroups[i]
    end
end
if #to_remove > 0 then
    redis.call('srem', KEYS[1], unpack(to_remove))
end

-- remove metagroups
for i=3 + no_groups * 2, #KEYS, 1 do
   redis.call('srem', KEYS[i], group_ref)
end

-- add subgroups to metagroup
if no_groups > 0 then
    redis.call('sadd', KEYS[1], unpack(ARGV, 3 + no_groups))

    -- add metagroup to subgroups
    for i=3 + no_groups, 2 + no_groups * 2, 1 do
        redis.call('sadd', KEYS[i], group_ref)
    end
end
"""

# keys = [meta_g_key, sub_g_key, meta_sg_key, sub_mg_key]
# args = [group, subgroup, meta_ref_key, sub_ref_key]
_remove_subgroup_script = """
if redis.call('sismember', KEYS[1], ARGV[1]) == 0 then
    return {err=ARGV[3]}
elseif redis.call('sismember', KEYS[2], ARGV[2]) == 0 then
    return {err=ARGV[4]}
end

if redis.call('srem', KEYS[3], ARGV[4]) == 0 then
    return {err=ARGV[4]}
end
redis.call('srem', KEYS[4], ARGV[3])
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

    TRANSACTION_MANAGER = RedisTransactionManager

    def __init__(self, HOST='localhost', PORT=6379, DB=0, **kwargs):
        self.redis = self._load_library()
        kwargs.setdefault('decode_responses', True)
        self.conn = self.redis.StrictRedis(host=HOST, port=PORT, db=DB, **kwargs)

        # register scripts
        self._create_user = self.conn.register_script(_create_user_script)
        self._rename_user = self.conn.register_script(_rename_user_script)
        self._set_password = self.conn.register_script(_set_password_script)
        self._remove_user = self.conn.register_script(_remove_user_script)
        self._create_property = self.conn.register_script(_create_property_script)
        self._set_property = self.conn.register_script(_set_property_script)
        self._set_properties = self.conn.register_script(_set_properties_script)
        self._remove_property = self.conn.register_script(_remove_property_script)
        self._rename_group = self.conn.register_script(_rename_group_script)
        self._set_service = self.conn.register_script(_set_service_script)
        self._set_memberships = self.conn.register_script(_set_memberships_script)
        self._add_member = self.conn.register_script(_add_member_script)
        self._remove_member = self.conn.register_script(_remove_member_script)
        self._add_subgroup = self.conn.register_script(_add_subgroup_script)
        self._set_subgroups = self.conn.register_script(_set_subgroups_script)
        self._remove_subgroup = self.conn.register_script(_remove_subgroup_script)

    # serialize a dictionary into a flat list including keys and values
    def _listify(self, d):
        l = []
        [l.extend(t) for t in six.iteritems(d)]
        return l

    # get the id of a service
    def _sid(self, service):
        return service.id if service is not None else 'None'

    # The key that lists groups of the given service
    def _g_key(self, service):
        return 'groups_%s' % (service.id if service is not None else 'None')

    # The key that is used to reference sub/meta-groups
    def _ref_key(self, group, service):
        return '%s_%s' % (service.id if service is not None else 'None', group)

    # The key that lists members of the given group
    def _gu_key(self, group, service):
        return 'members_%s_%s' % (service.id if service is not None else 'None', group)

    # The key that lists sub-groups of the given group
    def _sg_key(self, group, service):
        return 'subgroups_%s_%s' % (service.id if service is not None else 'None', group)

    # The key that lists meta-groups of the given group
    def _mg_key(self, group, service):
        return 'metagroups_%s_%s' % (service.id if service is not None else 'None', group)

    # parse any group key (members, subgroups, metagroups)
    def _parse_key(self, key):
        if six.PY2 and isinstance(key, str):
            key = key.decode('utf-8')

        sid, name = key.split('_')
        if sid == 'None':
            return (name, None)
        else:
            return (name, int(sid))

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        password = make_password(password) if password else ''
        properties = properties or {}
        groups = groups or []

        if dry is True:  # handle dry mode
            if self.conn.hexists('users', user):  # this is really the only error condition
                raise UserExists(user)
            return

        try:
            keys = ['users']
            group_keys = set()
            group_args = []
            for group, service in groups:
                group_keys.add(self._g_key(service))
                group_keys.add(self._gu_key(group, service))
                group_args += ['None' if service is None else str(service.id), group]

            properties = self._listify(properties)
            if properties:
                keys.append('props_%s' % user)

            keys += list(group_keys)
            args = [user, password, len(properties) + 3] + properties + group_args
            self._create_user(keys=keys, args=args)
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
            # TODO: handle groups
            keys = ['users', 'props_%s' % user, 'props_%s' % name]
            self._rename_user(keys=keys, args=[user, name])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            elif e.message == 'UserExists':
                raise UserExists(name)
            raise

    def check_password(self, user, password, groups=None):
        # TODO: rewrite as lua script
        if password is None:
            return False

        def setter(raw_password):
            self.set_password(user, raw_password)

        stored = self.conn.hget('users', user)
        if stored is None:
            raise UserNotFound(user)
        matches = check_password(password, stored, setter)

        if groups is not None:
            for group, service in groups:
                if self.is_member(group, service, user):
                    return True
            return False

        return matches

    def set_password(self, user, password=None):
        password = make_password(password) if password else ''

        try:
            self._set_password(keys=['users'], args=[user, password])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

    def set_password_hash(self, user, algorithm, hash):
        hash = import_hash(algorithm, hash)

        try:
            self._set_password(keys=['users'], args=[user, hash])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

    def remove_user(self, user):
        try:
            keys = ['users', 'props_%s' % user] + list(self.conn.scan_iter(match='members_*'))
            self._remove_user(keys=keys, args=[user])
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

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
            pipe.hexists('props_%s' % user, key)
            user_exists, prop_exists = pipe.execute()
            if user_exists is False:
                raise UserNotFound(user)
            elif prop_exists is True:
                raise PropertyExists(key)
            return

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

    def list_groups(self, service, user=None):
        if user is None:
            return list(self.conn.smembers(self._g_key(service)))
        else:
            # TODO: rewrite as lua script
            if not self.conn.hexists('users', user):
                raise UserNotFound(user)

            groups = set()
            for group in self.conn.smembers(self._g_key(service)):
                if self.is_member(group=group, service=service, user=user):
                    groups.add(group)
            return list(groups)

    def create_group(self, group, service, users=None, dry=False):
        # TODO: rewrite as lua script

        g_key = self._g_key(service)
        if self.conn.sismember(g_key, group):
            raise GroupExists(group)
        elif dry is True:
            return

        self.conn.sadd(g_key, group)

        # add users
        if users is not None:
            # multi value insert in lua - use unpack:
            # http://redis.io/commands/sadd#comment-800126580
            self.conn.sadd(self._gu_key(group, service), *users)

    def rename_group(self, group, name, service):
        sid = self._sid(service)
        g_key = self._g_key(service)
        old_gu_key = self._gu_key(group, service)
        new_gu_key = self._gu_key(name, service)
        old_sg_key = self._sg_key(group, service)
        new_sg_key = self._sg_key(name, service)
        mg_keys = ['metagroups_%s' % k for k in self.conn.smembers(old_sg_key)]

        keys = [g_key, old_gu_key, new_gu_key, old_sg_key, new_sg_key] + mg_keys
        args = [group, name, sid]

        try:
            self._rename_group(keys=keys, args=args)
        except self.redis.ResponseError as e:
            if e.message == 'GroupNotFound':
                raise GroupNotFound(group, service)
            elif e.message == 'GroupExists':
                raise GroupExists(name)
            raise

    def set_group_service(self, group, service, new_service):
        # TODO: This should be named set_service
        old_sid = self._sid(service)
        new_sid = self._sid(new_service)

        old_g_key = self._g_key(service)
        new_g_key = self._g_key(new_service)
        old_gu_key = self._gu_key(group, service)
        new_gu_key = self._gu_key(group, new_service)
        old_sg_key = self._sg_key(group, service)
        new_sg_key = self._sg_key(group, new_service)
        mg_keys = ['metagroups_%s' % k for k in self.conn.smembers(old_sg_key)]

        keys = [old_g_key, new_g_key, old_gu_key, new_gu_key, old_sg_key, new_sg_key] + mg_keys
        args = [group, old_sid, new_sid]

        try:
            self._set_service(keys=keys, args=args)
        except self.redis.ResponseError as e:
            if e.message == 'GroupNotFound':
                raise GroupNotFound(group, service)
            elif e.message == 'GroupExists':
                raise GroupExists(group)
            raise

    def group_exists(self, group, service):
        return self.conn.sismember(self._g_key(service), group)

    def set_memberships(self, user, service, groups):
        try:
            g_key = self._g_key(service)

            # All existing and created groups may be modified
            clear_groups = self.conn.smembers(g_key) | set(groups)
            keys = ['users', g_key] + [self._gu_key(g, service) for g in clear_groups]
            args = [user, self._sid(service)] + groups

            self._set_memberships(keys=keys, args=args)
        except self.redis.ResponseError as e:
            if e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

    def set_members(self, group, service, users):
        # TODO: rewrite as lua script

        # test that all users exist
        all_users = set(self.conn.hkeys('users'))
        for user in users:
            if user not in all_users:
                raise UserNotFound(user)

        if self.conn.sismember(self._g_key(service), group) is False:
            raise GroupNotFound(group, service)

        gu_key = self._gu_key(group, service)

        self.conn.delete(gu_key)  # clear set
        if users:  # only add if users is not empty
            self.conn.sadd(gu_key, *users)

    def add_member(self, group, service, user):
        try:
            self._add_member(keys=[self._g_key(service), 'users', self._gu_key(group, service)],
                             args=[group, user])
        except self.redis.ResponseError as e:
            if e.message == 'GroupNotFound':
                raise GroupNotFound(group, service)
            elif e.message == 'UserNotFound':
                raise UserNotFound(user)
            raise

    def _parents(self, ref_key, depth, max_depth):
        parents = self.conn.smembers('metagroups_%s' % ref_key)
        if depth < max_depth:
            for parent in set(parents):
                parents |= self._parents(parent, depth + 1, max_depth)
        return parents

    def members(self, group, service, depth=None):
        # TODO: rewrite as lua script

        if depth is None:
            depth = settings.GROUP_RECURSION_DEPTH

        g_key = self._g_key(service)
        if not self.conn.sismember(g_key, group):
            raise GroupNotFound(group, service)

        members = self.conn.smembers(self._gu_key(group, service))
        if depth == 0:
            return list(members)
        ref_keys = self._parents(self._ref_key(group, service), depth=1, max_depth=depth)
        ref_keys = ['members_%s' % k for k in ref_keys]
        if ref_keys:
            return list(members | self.conn.sunion(*ref_keys))
        else:
            return list(members)

    def is_member(self, group, service, user):
        # TODO: rewrite as lua script
        g_key = self._g_key(service)
        if not self.conn.sismember(g_key, group):
            raise GroupNotFound(group, service)

        members = self.conn.smembers(self._gu_key(group, service))
        if user in members:
            return True

        ref_keys = self._parents(self._ref_key(group, service), depth=1,
                                 max_depth=settings.GROUP_RECURSION_DEPTH)
        ref_keys = ['members_%s' % k for k in ref_keys]
        if ref_keys:  # we might have no parents
            return user in self.conn.sunion(*ref_keys)
        return False

    def remove_member(self, group, service, user):
        try:
            self._remove_member(keys=[self._g_key(service), self._gu_key(group, service)],
                                args=[group, user])
        except self.redis.ResponseError as e:
            if e.message == 'GroupNotFound':
                raise GroupNotFound(group, service)
            elif e.message == "UserNotFound":
                raise UserNotFound(user)
            raise

    def add_subgroup(self, group, service, subgroup, subservice):
        g_key = self._g_key(service)
        sg_key = self._g_key(subservice)

        keys = [g_key, sg_key, self._sg_key(group, service), self._mg_key(subgroup, subservice)]
        args = [group, subgroup, self._ref_key(group, service), self._ref_key(subgroup, subservice)]
        try:
            self._add_subgroup(keys=keys, args=args)
        except self.redis.ResponseError as e:
            raise GroupNotFound(*self._parse_key(e.message))

    def set_subgroups(self, group, service, subgroups, subservice):
        # TODO: subgroups should be a list of tuples with service
        sg_key = self._sg_key(group, service)  # stores subgroups
        g_key = self._g_key(service)  # test for existence here
        g_keys = [self._g_key(subservice) for g in subgroups]  # test for existence here
        ref_keys = [self._ref_key(g, subservice) for g in subgroups]  # used for reference
        mg_keys = [self._mg_key(g, subservice) for g in subgroups]  # stores metagroup

        # get metagroup keys with the same service
        sid = self._sid(service)
        add_mg_keys = ['metagroups_%s' % k for k in self.conn.smembers(sg_key) if
                       k.startswith('%s_' % sid)]

        keys = [sg_key, g_key, ] + g_keys + mg_keys + [k for k in add_mg_keys if k not in mg_keys]
        args = [sid, group, ] + subgroups + ref_keys
        try:
            self._set_subgroups(keys=keys, args=args)
        except self.redis.ResponseError:
            # TODO: we do not yet pass the correct value
            raise GroupNotFound(group, service=None)

    def is_subgroup(self, group, service, subgroup, subservice):
        return self.conn.sismember(self._sg_key(group, service),
                                   self._ref_key(subgroup, subservice))

    def subgroups(self, group, service, filter=True):
        g_key = self._g_key(service)
        if not self.conn.sismember(g_key, group):
            raise GroupNotFound(group, service)

        if filter is True:
            sid = None if service is None else service.id
            subgroups = [self._parse_key(k) for k in self.conn.smembers(self._sg_key(group, service))]
            return [g for g, s in subgroups if s == sid]
        else:
            subgroups = [self._parse_key(k) for k in self.conn.smembers(self._sg_key(group, service))]
            return [(g, (Service.objects.get(id=s) if s is not None else None)) for g, s in subgroups]

    def parents(self, group, service):
        g_key = self._g_key(service)
        if not self.conn.sismember(g_key, group):
            raise GroupNotFound(group, service)

        parents = [self._parse_key(k) for k in self.conn.smembers(self._mg_key(group, service))]
        return [(g, Service.objects.get(id=s) if s is not None else None) for g, s in parents]

    def remove_subgroup(self, group, service, subgroup, subservice):
        # to test for existence
        meta_g_key = self._g_key(service)
        sub_g_key = self._g_key(subservice)
        meta_ref_key = self._ref_key(group, service)
        sub_ref_key = self._ref_key(subgroup, subservice)
        meta_sg_key = self._sg_key(group, service)
        sub_mg_key = self._mg_key(subgroup, subservice)

        keys = [meta_g_key, sub_g_key, meta_sg_key, sub_mg_key]
        args = [group, subgroup, meta_ref_key, sub_ref_key]

        try:
            self._remove_subgroup(keys=keys, args=args)
        except self.redis.ResponseError as e:
            raise GroupNotFound(*self._parse_key(e.message))

    def remove_group(self, group, service):
        if self.conn.srem(self._g_key(service), group) == 0:
            raise GroupNotFound(group, service)

        ref_key = self._ref_key(group, service)
        mg_key = self._mg_key(group, service)
        sg_key = self._sg_key(group, service)

        # get list of metagroups/subgroups
        metagroups = self.conn.smembers(mg_key)
        subgroups = self.conn.smembers(sg_key)

        for mg in ['subgroups_%s' % g for g in metagroups]:
            self.conn.srem(mg, ref_key)
        for sg in ['metagroups_%s' % g for g in subgroups]:
            self.conn.srem(sg, ref_key)

        self.conn.delete(mg_key, sg_key)

    def testSetUp(self):
        self.conn.flushdb()

    def testTearDown(self):
        self.conn.flushdb()
