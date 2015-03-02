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

from collections import defaultdict
from copy import deepcopy

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.utils import six

from backends.base import BackendBase
from common.errors import GroupExists
from common.errors import GroupNotFound
from common.errors import PropertyExists
from common.errors import PropertyNotFound
from common.errors import UserExists
from common.errors import UserNotFound
from common.hashers import import_hash


class MemoryTransactionManager(object):
    def __init__(self, backend, dry=False):
        self.backend = backend
        self.dry = dry

    def __enter__(self):
        self.users = deepcopy(self.backend._users)
        self.groups = deepcopy(self.backend._groups)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.dry or exc_type:
            self.backend._users = self.users
            self.backend._groups = self.groups


class MemoryBackend(BackendBase):
    TRANSACTION_MANAGER = MemoryTransactionManager

    def __init__(self):
        self._users = {}
        self._groups = defaultdict(dict)

    def testSetUp(self):
        self._users = {}
        self._groups = defaultdict(dict)

    def testTearDown(self):
        self._users = {}
        self._groups = defaultdict(dict)

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        if user in self._users:
            raise UserExists(user)
        if dry is False:
            self._users[user] = {
                'password': None,
                'properties': properties or {},
            }
            if password:
                self._users[user]['password'] = make_password(password)
            if groups is not None:
                for group, service in groups:
                    # auto-create groups
                    if self.group_exists(group=group, service=service):
                        self.add_member(group=group, service=service, user=user)
                    else:
                        self.create_group(group=group, service=service, users=[user])

    def list_users(self):
        return self._users.keys()

    def user_exists(self, user):
        return user in self._users

    def rename_user(self, user, name):
        if name in self._users:
            raise UserExists(name)

        try:
            self._users[name] = self._users.pop(user)
        except KeyError:
            raise UserNotFound(user)

    def check_password(self, user, password, groups=None):
        try:
            stored = self._users[user]['password']
        except KeyError:
            raise UserNotFound(user)

        def setter(raw_password):
            self.set_password(user, raw_password)

        if not password or not check_password(password, stored, setter):
            return False

        if groups is None:
            return True
        for group, service in groups:
            if self.is_member(group, service, user):
                return True
        return False

    def set_password(self, user, password=None):
        try:
            if password:
                self._users[user]['password'] = make_password(password)
            else:
                self._users[user]['password'] = None
        except KeyError:
            raise UserNotFound(user)

    def set_password_hash(self, user, algorithm, hash):
        django_hash = import_hash(algorithm, hash)
        self._users[user]['password'] = django_hash

    def remove_user(self, user):
        try:
            del self._users[user]
        except KeyError:
            raise UserNotFound(user)

    def list_properties(self, user):
        try:
            return self._users[user]['properties'].copy()
        except KeyError:
            raise UserNotFound(user)

    def create_property(self, user, key, value, dry=False):
        try:
            properties = self._users[user]['properties']
        except KeyError:
            raise UserNotFound(user)

        if key in properties:
            raise PropertyExists(key)

        if dry is False:  # TODO: can we use properties variable instead?
            self._users[user]['properties'][key] = value

    def get_property(self, user, key):
        try:
            properties = self._users[user]['properties']
        except KeyError:
            raise UserNotFound(user)
        try:
            return properties[key]
        except KeyError:
            raise PropertyNotFound(key)

    def set_property(self, user, key, value):
        try:
            properties = self._users[user]['properties']
        except KeyError:
            raise UserNotFound(user)

        old_value = properties.get(key)
        properties[key] = value
        return old_value

    def set_properties(self, user, properties):
        try:
            existing_properties = self._users[user]['properties']
        except KeyError:
            raise UserNotFound(user)

        existing_properties.update(properties)

    def remove_property(self, user, key):
        try:
            properties = self._users[user]['properties']
        except KeyError:
            raise UserNotFound(user)

        try:
            del properties[key]
        except KeyError:
            raise PropertyNotFound(key)

    def list_groups(self, service, user=None):
        if user is None:
            return self._groups[service].keys()
        elif user not in self._users:
            raise UserNotFound(user)
        else:
            return [k for k, v in six.iteritems(self._groups[service])
                    if self.is_member(k, service, user)]

    def create_group(self, group, service=None, users=None, dry=False):
        if group in self._groups[service]:
            raise GroupExists(group)
        if users is not None and not set(self._users.keys()) >= set(users):
            raise UserNotFound()

        if dry is False:
            self._groups[service][group] = {
                'users': set(users) if users else set(),
                'meta-groups': set(),
                'sub-groups': set(),
            }

    def rename_group(self, group, name, service=None):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        elif name in self._groups[service]:
            raise GroupExists(name)

        self._groups[service][name] = self._groups[service].pop(group)

    def set_group_service(self, group, service=None, new_service=None):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        if group in self._groups[new_service]:
            raise GroupExists(group)

        self._groups[new_service][group] = self._groups[service].pop(group)

    def group_exists(self, group, service=None):  #TODO: service should not be optional!
        return group in self._groups[service]

    def set_memberships(self, user, service, groups):
        if user not in self._users:
            raise UserNotFound(user)

        # delete existing memberships
        for group in self._groups[service]:
            if user in self._groups[service][group]['users']:
                self._groups[service][group]['users'].remove(user)

        # set new memberships
        for group in groups:
            if self.group_exists(group=group, service=service):
                self.add_member(group=group, service=service, user=user)
            else:
                self.create_group(group=group, service=service, users=[user])

    def set_members(self, group, service, users):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        for user in filter(lambda u: u not in self._users, users):
            raise UserNotFound(user)

        self._groups[service][group]['users'] = set(users)

    def add_member(self, group, service, user):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        if user not in self._users:
            raise UserNotFound(user)
        self._groups[service][group]['users'].add(user)

    def _members(self, group, service, depth, max_depth):
        members = set(self._groups[service][group]['users'])
        if depth < max_depth:
            for meta_group, meta_service in self._groups[service][group]['meta-groups']:
                members |= self._members(meta_group, meta_service,
                                         depth=depth + 1, max_depth=max_depth)

        return members

    def members(self, group, service, depth=None):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        if depth is None:
            depth = settings.GROUP_RECURSION_DEPTH

        members = set(self._groups[service][group]['users'])

        if depth > 0:
            for meta_group, meta_service in self._groups[service][group]['meta-groups']:
                members |= self._members(meta_group, meta_service, depth=1, max_depth=depth)

        return list(members)

    def _is_member(self, group, service, user, depth=0):
        if user in self._groups[service][group]['users']:
            return True

        if depth <= settings.GROUP_RECURSION_DEPTH:
            for meta_group, meta_service in self._groups[service][group]['meta-groups']:
                if self._is_member(group=meta_group, service=meta_service, user=user, depth=depth + 1):
                    return True
        return False

    def is_member(self, group, service, user):
        if group not in self._groups[service]:
            raise GroupNotFound(group)

        return self._is_member(group, service, user)

    def remove_member(self, group, service, user):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        try:
            self._groups[service][group]['users'].remove(user)
        except KeyError:
            raise UserNotFound(user)

    def add_subgroup(self, group, service, subgroup, subservice):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        if subgroup not in self._groups[subservice]:
            raise GroupNotFound(subgroup)

        self._groups[service][group]['sub-groups'].add((subgroup, subservice))
        self._groups[subservice][subgroup]['meta-groups'].add((group, service))

    def set_subgroups(self, group, service, subgroups, subservice):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        for subgroup in filter(lambda g: g not in self._groups[subservice], subgroups):
            raise GroupNotFound(subgroup)

        # clear any existing sub-groups from the same service
        for current_subgroup, current_subservice in filter(
                lambda t: t[1] == service, self._groups[service][group]['sub-groups']):
            self._groups[current_subservice][current_subgroup]['meta-groups'].remove((group, service))
        cleared = [(g, s) for g, s in self._groups[service][group]['sub-groups'] if s != service]
        self._groups[service][group]['sub-groups'] = set(cleared)

        # add bi-directional relationship
        for subgroup in subgroups:
            self._groups[subservice][subgroup]['meta-groups'].add((group, service))

        # we update s because there might be left-over subgroups from a different service
        self._groups[service][group]['sub-groups'] |= set([(subgroup, subservice) for subgroup in subgroups])

    def is_subgroup(self, group, service, subgroup, subservice):
        if group not in self._groups[service]:
            raise GroupNotFound(group)

        return (subgroup, subservice) in self._groups[service][group]['sub-groups']

    def remove_subgroup(self, group, service, subgroup, subservice):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        if subgroup not in self._groups[subservice]:
            raise GroupNotFound(subgroup)

        try:
            self._groups[service][group]['sub-groups'].remove((subgroup, subservice))
            self._groups[service][subgroup]['meta-groups'].remove((group, service))
        except KeyError:
            raise GroupNotFound(subgroup)

    def subgroups(self, group, service, filter=True):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        if filter is True:
            return [g for g, s in self._groups[service][group]['sub-groups'] if s == service]
        else:
            return list(self._groups[service][group]['sub-groups'])

    def parents(self, group, service):
        if group not in self._groups[service]:
            raise GroupNotFound(group)
        return list(self._groups[service][group]['meta-groups'])

    def remove_group(self, group, service):
        if group not in self._groups[service]:
            raise GroupNotFound(group)

        del self._groups[service][group]
