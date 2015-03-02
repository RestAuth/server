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

from __future__ import unicode_literals, absolute_import

#import warnings

from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import six

from Groups.models import Group
from Users.models import Property
from Users.models import ServiceUser as User
from backends.base import BackendBase
from common.hashers import import_hash
from common.errors import GroupExists
from common.errors import GroupNotFound
from common.errors import PropertyExists
from common.errors import PropertyNotFound
from common.errors import UserExists
from common.errors import UserNotFound


class DjangoTransactionManager(object):
    def __init__(self, dry=False, using=None):
        self.dry = dry
        self.using = using

    def __enter__(self):
        transaction.set_autocommit(False, using=None)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.dry or exc_type:
                transaction.rollback(using=self.using)
            else:
                transaction.commit(using=self.using)
        finally:
            transaction.set_autocommit(True, using=self.using)


class DjangoBackend(BackendBase):
    def __init__(self, USING=None):
        self.db = USING

    def _user(self, username, *fields):
        try:
            return User.objects.only(*fields).get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def _group(self, name, service, *fields):
        try:
            return Group.objects.only(*fields).get(name=name, service=service)
        except Group.DoesNotExist:
            raise GroupNotFound(name, service=service)

    def transaction(self, dry=False):
        return DjangoTransactionManager(dry=dry, using=self.db)

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        with self.transaction(dry=dry):
            try:
                user = User(username=user)
                user.set_password(password)
                if password is not None and password != '':
                    user.set_password(password)
                user.save()
            except IntegrityError:
                raise UserExists("A user with the given name already exists.")

            if properties:  # create properties
                user.create_properties(properties)

            if groups:  # add groups
                _groups = []
                for name, service in groups:
                    try:
                        _groups.append(Group.objects.get(service=service, name=name))
                    except Group.DoesNotExist:
                        _groups.append(Group.objects.create(service=service, name=name))
                user.group_set.add(*_groups)

    def list_users(self):
        return list(User.objects.values_list('username', flat=True))

    def user_exists(self, user):
        return User.objects.filter(username=user).exists()

    def rename_user(self, user, name):
        user = self._user(user, 'username')
        user.username = name
        try:
            user.save()
        except IntegrityError:
            raise UserExists("User already exists.")

    def check_password(self, user, password, groups=None):
        if not self._user(user, 'password').check_password(password):
            return False  # return fast if password is incorrect.
        if groups is None:
            return True  # if no groups are given, we're ok.

        # TODO: this could be faster. from list_groups:
        # groups = Group.objects.member(user=user, service=service)
        # return list(groups.only('name').values_list('name', flat=True))
        for group, service in groups:
            if self.is_member(group=group, service=service, user=user):
                return True
        return False

    def set_password(self, user, password=None):
        user = self._user(user, 'id', 'password')

        if password is not None and password != '':
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

    def set_password_hash(self, user, algorithm, hash):
        user = self._user(user, 'password')
        user.password = import_hash(algorithm=algorithm, hash=hash)
        user.save()

    def remove_user(self, user):
        qs = User.objects.filter(username=user)
        if qs.exists():
            qs.delete()
        else:
            raise UserNotFound(user)

    def list_properties(self, user):
        qs = Property.objects.filter(user__username=user)
        properties = dict(qs.values_list('key', 'value'))
        if not properties and not self.user_exists(user=user):
            raise UserNotFound(user)
        return properties

    def create_property(self, user, key, value, dry=False):
        with self.transaction(dry=dry):
            try:
                user = self._user(user, 'id')
                user.property_set.create(key=key, value=value)
            except IntegrityError:
                raise PropertyExists()

    def get_property(self, user, key):
        try:
            user = self._user(user, 'id')
            return user.property_set.only('value').get(key=key).value
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def set_property(self, user, key, value):
        user = self._user(user, 'id')
        prop, old_value = user.set_property(key, value)
        return old_value

    def set_properties(self, user, properties):
        user = self._user(user, 'id')
        for key, value in six.iteritems(properties):
            user.set_property(key, value)

    def remove_property(self, user, key):
        try:
            user = self._user(user, 'id')
            user.del_property(key)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def list_groups(self, service, user=None):
        if user is None:
            groups = Group.objects.filter(service=service)
        else:
            user = self._user(user, 'id')
            groups = Group.objects.member(user=user, service=service)
        return list(groups.only('name').values_list('name', flat=True))

    def create_group(self, group, service=None, users=None, dry=False):
        with self.transaction(dry=dry):
            try:
                group = Group.objects.create(name=group, service=service)
                if users:
                    user_objs = User.objects.only('id').filter(username__in=users)
                    if len(users) != len(user_objs):
                        raise UserNotFound()
                    group.users.add(*user_objs)
            except IntegrityError:
                raise GroupExists(group)

    def rename_group(self, group, name, service=None):
        try:
            group = self._group(group, service, 'id', 'name')
            group.name = name
            group.save()
        except IntegrityError:
            raise GroupExists(name)

    def set_group_service(self, group, service=None, new_service=None):
        try:
            updated = Group.objects.filter(name=group, service=service).update(service=new_service)
            if updated == 0:
                raise GroupNotFound(group, service=service)
#            group = self._group(group, service, 'id')
#            group.service = new_service
#            group.save()
        except IntegrityError:
            raise GroupExists(group)

    def group_exists(self, group, service=None):
        return Group.objects.filter(name=group, service=service).exists()

    def set_memberships(self, user, service, groups):
        user = self._user(user, 'id')

        user.group_set.through.objects.filter(
            group__service=service, serviceuser_id=user.id).delete()
        groups = [Group.objects.get_or_create(service=service, name=name)[0] for name in groups]
        user.group_set.add(*groups)

    def set_members(self, group, service, users):
        group = self._group(group, service, 'id')
        users = [self._user(u, 'id') for u in users]
        group.users.clear()
        group.users.add(*users)

    def add_member(self, group, service, user):
        group = self._group(group, service, 'id')
        user = self._user(user, 'id')
        group.users.add(user)

    def members(self, group, service, depth=None):
        group = self._group(group, service, 'id')
        return list(group.get_members(depth=depth).values_list('username', flat=True))

    def is_member(self, group, service, user):
        group = self._group(group, service, 'id')
        return group.is_member(user)

    def remove_member(self, group, service, user):
        group = self._group(group, service, 'id')
        user = self._user(user, 'id')

        if group.is_member(user):
            group.users.remove(user)
        else:
            raise UserNotFound(user.username)  # 404 Not Found

    def add_subgroup(self, group, service, subgroup, subservice):
        group = self._group(group, service, 'id')
        subgroup = self._group(subgroup, subservice, 'id')
        group.groups.add(subgroup)

    def set_subgroups(self, group, service, subgroups, subservice):
        group = self._group(group, service, 'id')
        subgroups = [self._group(name, subservice, 'id') for name in subgroups]

        group.groups.through.objects.filter(from_group=group, to_group__service=subservice).delete()
        group.groups.add(*subgroups)

    def is_subgroup(self, group, service, subgroup, subservice):
        group = self._group(group, service, 'id')
        subgroup = self._group(subgroup, subservice, 'id')
        return group.groups.filter(pk=subgroup.id).exists()

    def remove_subgroup(self, group, service, subgroup, subservice):
        group = self._group(group, service, 'id')
        try:
            subgroup = group.groups.get(name=subgroup, service=subservice)
        except Group.DoesNotExist:
            raise GroupNotFound(subgroup, service=subservice)

        group.groups.remove(subgroup)

    def subgroups(self, group, service, filter=True):
        group = self._group(group, service, 'id')

        if filter:
            qs = group.groups.filter(service=service)
            return list(qs.values_list('name', flat=True))
        else:
            return [(g.name, g.service) for g in group.groups.select_related('service').all()]

    def parents(self, group, service):
        group = self._group(group, service, 'id')
        return [(g.name, g.service) for g in group.parent_groups.select_related('service').all()]

    def remove_group(self, group, service):
        group = self._group(group, service, 'id')
        group.delete()
