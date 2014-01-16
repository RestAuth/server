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

from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.utils import six

from backends.base import GroupInstance
from backends.base import UserInstance
from common.errors import GroupExists
from common.errors import GroupNotFound
from common.errors import PropertyExists
from common.errors import PropertyNotFound
from common.errors import UserExists
from common.errors import UserNotFound


class MemoryUserInstance(UserInstance):
    def __init__(self, id, username, password=None):
        super(MemoryUserInstance, self).__init__(id, username)
        self.password = password


class MemoryGroupInstance(GroupInstance):
    def __init__(self, id, name, service):
        super(MemoryGroupInstance, self).__init__(id, name, service)
        self._members = set()
        self.parents = set()
        self.children = set()

    def add_user(self, user):
        self._members.add(user.username)

    def rm_user(self, user):
        try:
            self._members.remove(user.username)
        except KeyError:
            raise UserNotFound(user.username)

    def members(self, depth=None):
        users = self._members.copy()
        if depth == 0:
            return users

        if depth is None:
            depth = settings.GROUP_RECURSION_DEPTH

        for parent in self.parents:
            users |= parent.members(depth=depth - 1)
        return users

    def is_member(self, user):
        return user.username in self.members()

    def subgroups(self, filter=True):
        if filter:
            return [g for g in self.children if g.service == self.service]
        else:
            return self.children.copy()

    def add_subgroup(self, subgroup):
        subgroup.parents.add(self)
        self.children.add(subgroup)

    def rm_subgroup(self, subgroup):
        try:
            self.children.remove(subgroup)
            subgroup.parents.remove(self)
        except KeyError:
            raise GroupNotFound(subgroup.name)

    def __eq__(self, other):
        return self.service == other.service and self.name == other.name


class MemoryUserBackend(object):
    """Dummy backend that stores all users in memory (for debugging purposes).

    Please note the obvious: This backend should *never be used in a production
    environment*. Any restart of the server software will completely wipe all
    data.
    """

    def __init__(self):
        self._users = {}

    def get(self, username):
        try:
            return self._users[username]
        except KeyError:
            raise UserNotFound(username)

    def list(self):
        return six.iterkeys(self._users)

    def create(self, username, password=None, properties=None,
               property_backend=None, dry=False, transaction=True):
        if username in self._users:
            raise UserExists(username)

        user_id = id(username)
        user = MemoryUserInstance(user_id, username, password)

        if properties is None:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            properties = {'date joined': stamp}
        elif 'date joined' not in properties:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            properties['date joined'] = stamp

        property_backend.set_multiple(user, properties, dry=dry,
                                      transaction=transaction)

        if not dry:
            self._users[username] = user
        return user

    def exists(self, username):
        return username in self._users

    def check_password(self, username, password):
        try:
            user = self._users[username]
            if user.password is None or user.password == '':
                return False
            return user.password == password
        except KeyError:
            raise UserNotFound(username)

    def set_password(self, username, password=None):
        try:
            self._users[username].password = password
        except KeyError:
            raise UserNotFound(username)

    def remove(self, username):
        try:
            del self._users[username]
        except KeyError:
            raise UserNotFound(username)

    def testSetUp(self):
        pass

    def testTearDown(self):
        self._users = {}


class MemoryPropertyBackend(object):
    """Dummy backend that stores all properties in memory (for debugging).

    Please note the obvious: This backend should *never be used in a production
    environment*. Any restart of the server software will completely wipe all
    data.
    """

    def __init__(self):
        self._properties = defaultdict(dict)

    def list(self, user):
        return dict(self._properties[user.username])

    def create(self, user, key, value, dry=False):
        name = user.username
        if key in self._properties[name]:
            raise PropertyExists(name)

        if not dry:
            self._properties[name][key] = value

        return key, value

    def get(self, user, key):
        try:
            return self._properties[user.username][key]
        except KeyError:
            raise PropertyNotFound(key)

    def set(self, user, key, value, dry=False, transaction=True):
        old = self._properties[user.username].get(key, None)
        if not dry:
            self._properties[user.username][key] = value
        return key, old

    def set_multiple(self, user, props, dry=False, transaction=True):
        if not dry:
            self._properties[user.username].update(props)

    def remove(self, user, key):
        try:
            del self._properties[user.username][key]
        except KeyError:
            raise PropertyNotFound(key)

    def testSetUp(self):
        pass

    def testTearDown(self):
        self._properties = defaultdict(dict)


class MemoryGroupBackend(object):
    """Dummy backend that stores all groups in memory (for debugging).

    Please note the obvious: This backend should *never be used in a production
    environment*. Any restart of the server software will completely wipe all
    data.
    """

    def __init__(self):
        self._groups = defaultdict(dict)

    def get(self, name, service=None):
        try:
            return self._groups[self._service(service)][name]
        except KeyError:
            raise GroupNotFound(name)

    def _service(self, service):
        if service is None:
            return service
        else:
            return service.id

    def list(self, service, user=None):
        if user is None:
            return six.iterkeys(self._groups[self._service(service)])
        else:
            groups = self._groups[self._service(service)]
            return [k for k, v in six.iteritems(groups) if v.is_member(user)]

    def create(self, name, service=None, dry=False, transaction=True):
        if name in self._groups[self._service(service)]:
            raise GroupExists(name)
        group = MemoryGroupInstance(service=service, id=id(name), name=name)

        if not dry:
            self._groups[self._service(service)][name] = group

        return group

    def exists(self, name, service=None):
        return name in self._groups[self._service(service)]

    def add_user(self, group, user):
        self._groups[self._service(group.service)][group.name].add_user(user)

    def members(self, group, depth=None):
        return list(group.members(depth=depth))

    def is_member(self, group, user):
        return group.is_member(user)

    def rm_user(self, group, user):
        return group.rm_user(user)

    def add_subgroup(self, group, subgroup):
        group.add_subgroup(subgroup)

    def subgroups(self, group, filter=True):
        subgroups = group.subgroups(filter=filter)
        if filter:
            return [g.name for g in subgroups]
        else:
            return subgroups

    def rm_subgroup(self, group, subgroup):
        group.rm_subgroup(subgroup)

    def remove(self, group):
        service_id = self._service(group.service)
        if group.name in self._groups[service_id]:
            del self._groups[service_id][group.name]
        else:
            raise GroupNotFound(group.name)

    def parents(self, group):
        return list(group.parents)

    def testSetUp(self):
        pass

    def testTearDown(self):
        self._groups = defaultdict(dict)
