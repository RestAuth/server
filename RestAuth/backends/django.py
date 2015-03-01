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
    def __init__(self, dry, using=None):
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
            raise GroupNotFound(name)

    def atomic(self, dry=False):
        return DjangoTransactionManager(dry=dry, using=self.db)

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        with self.atomic(dry=dry):
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

    def user_exists(self, username):
        return User.objects.filter(username=username).exists()

    def rename_user(self, username, name):
        user = self._user(username, 'username')
        user.username = name
        try:
            user.save()
        except IntegrityError:
            raise UserExists("User already exists.")

    def check_password(self, username, password):
        return self._user(username, 'password').check_password(password)

    def set_password(self, username, password=None):
        user = self._user(username, 'id')

        if password is not None and password != '':
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

    def set_password_hash(self, username, algorithm, hash):
        user = self._user(username, 'password')

        user.password = import_hash(algorithm=algorithm, hash=hash)
        user.save()

    def remove_user(self, username):
        qs = User.objects.filter(username=username)
        if qs.exists():
            qs.delete()
        else:
            raise UserNotFound(username)

    def list_properties(self, username):
        qs = Property.objects.filter(user__username=username)
        properties = dict(qs.values_list('key', 'value'))
        if not properties and not self.user_exists(username=username):
            raise UserNotFound(username)
        return properties

    def create_property(self, username, key, value, dry=False):
        with self.atomic(dry=dry):
            try:
                user = User.objects.only('id').get(username=username)
                user.property_set.create(key=key, value=value)
            except User.DoesNotExist:
                raise UserNotFound(username)
            except IntegrityError:
                raise PropertyExists()

    def get_property(self, username, key):
        try:
            user = User.objects.only('id').get(username=username)
            return user.property_set.only('value').get(key=key).value
        except User.DoesNotExist:
            raise UserNotFound(username)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def set_property(self, username, key, value, dry=False):
        try:
            user = User.objects.only('id').get(username=username)
            prop, old_value = user.set_property(key, value)
            return old_value
        except User.DoesNotExist:
            raise UserNotFound(username)

    def set_multiple_properties(self, username, properties):
        try:
            user = User.objects.only('id').get(username=username)
            for key, value in six.iteritems(properties):
                user.set_property(key, value)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def remove_property(self, username, key):
        try:
            user = User.objects.only('id').get(username=username)
            user.del_property(key)
        except User.DoesNotExist:
            raise UserNotFound(username)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def list_groups(self, service=None, username=None):
        if username is None:
            groups = Group.objects.filter(service=service)
        else:
            try:
                user = User.objects.only('id').get(username=username)
                groups = Group.objects.member(user=user, service=service)
            except User.DoesNotExist:
                raise UserNotFound(username)
        return list(groups.only('name').values_list('name', flat=True))

    def create_group(self, name, service=None, users=None, dry=False):
        with self.atomic(dry=dry):
            try:
                group = Group.objects.create(name=name, service=service)
                if users:
                    user_objs = User.objects.only('id').filter(username__in=users)
                    if len(users) != len(user_objs):
                        raise UserNotFound()
                    group.users.add(*user_objs)
            except IntegrityError:
                raise GroupExists(name)

    def rename_group(self, name, new_name, service=None):
        try:
            group = self._group(name, service, 'id')
            group.name = new_name
            group.save()
        except IntegrityError:
            raise GroupExists(new_name)

    def set_group_service(self, name, service=None, new_service=None):
        try:
            group = self._group(name, service, 'id')
            group.service = new_service
            group.save()
        except IntegrityError:
            raise GroupExists(name)

    def group_exists(self, name, service=None):
        return Group.objects.filter(name=name, service=service).exists()

    def set_groups_for_user(self, user, service, groups):
        user = self._user(user, 'id')

        user.group_set.through.objects.filter(
            group__service=service, serviceuser_id=user.id).delete()
        groups = [Group.objects.get_or_create(service=service, name=name)[0] for name in groups]
        user.group_set.add(*groups)

    def set_users_for_group(self, group, service, users):
        group = self._group(group, service, 'id')
        users = [self._user(u, 'id') for u in users]
        group.users.clear()
        group.users.add(*users)

    def add_user(self, group, service, user):
        group = self._group(group, service, 'id')
        user = self._user(user, 'id')
        group.users.add(user)

    def members(self, group, service, depth=None):
        group = self._group(group, service, 'id')
        return list(group.get_members(depth=depth).values_list('username', flat=True))

    def is_member(self, group, service, user):
        group = self._group(group, service, 'id')
        return group.is_member(user)

    def rm_user(self, group, service, user):
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

    def rm_subgroup(self, group, service, subgroup, subservice):
        group = self._group(group, service, 'id')
        try:
            subgroup = group.groups.get(name=subgroup, service=subservice)
        except Group.DoesNotExist:
            raise GroupNotFound(subgroup)

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
