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

#import waarnings

from django.contrib.auth.models import User as BaseUser
from django.db import transaction as dj_transaction
from django.db.utils import IntegrityError
from django.utils import six

from Groups.models import Group
from Users.models import Property
from Users.models import ServiceUser as User
from backends.base import BackendBase
from backends.base import GroupBackend
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
        dj_transaction.set_autocommit(False, using=None)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.dry or exc_type:
                dj_transaction.rollback(using=self.using)
            else:
                dj_transaction.commit(using=self.using)
        finally:
            dj_transaction.set_autocommit(True, using=self.using)

    #TODO: Can be removed:
    def __eq__(self, other):
        return isinstance(other, type(self))

    #TODO: Can be removed:
    def __hash__(self):
        return hash(type(self))


class DjangoBackend(BackendBase):
    def __init__(self, USING=None):
        self.db = USING

    def _user(self, username, *fields):
        try:
            return User.objects.only(*fields).get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def atomic(self, dry=False):
        return DjangoTransactionManager(dry=dry, using=self.db)

    def get(self, username):
        #TODO: Remove this function
        #warnings.warn("Deprecated!")
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def create_user(self, username, password=None, properties=None, groups=None, dry=False):
        with self.atomic(dry=dry):
            try:
                user = User(username=username)
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

        return user  #TODO: We should not need to return anything!

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

            return group

    #def rename(self, group, name):
    def rename_group(self, name, new_name, service=None):
        try:
            group = Group.objects.get(name=name, service=service)
            group.name = new_name
            group.save()
        except Group.DoesNotExist:
            raise GroupNotFound(name)
        except IntegrityError:
            raise GroupExists(new_name)

    #def set_service(self, group, service=None):
    def set_group_service(self, name, service=None, new_service=None):
        try:
            group = Group.objects.get(name=name, service=service)
            group.service = new_service
            group.save()
        except Group.DoesNotExist:
            raise GroupNotFound(name)
        except IntegrityError:
            raise GroupExists(name)

    def group_exists(self, name, service=None):
        return Group.objects.filter(name=name, service=service).exists()

    def set_groups_for_user(self, user, service, groups):
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            raise UserNotFound(user)

        user.group_set.filter(service=service).delete()  # clear existing groups
        groups = [Group.objects.get_or_create(service=service, name=name)[0] for name in groups]
        user.group_set.add(*groups)

    def set_users_for_group(self, group, service, users):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
            users = [User.objects.only('id').get(username=u) for u in users]
        except Group.DoesNotExist:
            raise GroupNotFound(group)
        except User.DoesNotExist:
            raise UserNotFound()

        group.users.clear()
        group.users.add(*users)

    def add_user(self, group, service, user):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
            user = User.objects.only('id').get(username=user)
            group.users.add(user)
        except Group.DoesNotExist:
            raise GroupNotFound(group)
        except User.DoesNotExist:
            raise UserNotFound()

    def members(self, group, service, depth=None):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
        except Group.DoesNotExist:
            raise GroupNotFound(group)
        return list(group.get_members(depth=depth).values_list('username', flat=True))

    def is_member(self, group, service, user):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
        except Group.DoesNotExist:
            raise GroupNotFound(group)

        return group.is_member(user)

    def rm_user(self, group, service, user):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
            user = User.objects.only('id').get(username=user)
        except Group.DoesNotExist:
            raise GroupNotFound(group)
        except User.DoesNotExist:
            raise UserNotFound(user)

        if group.is_member(user):
            group.users.remove(user)
        else:
            raise UserNotFound(user.username)  # 404 Not Found

    def add_subgroup(self, group, service, subgroup, subservice):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
        except Group.DoesNotExist:
            raise GroupNotFound(group)
        try:
            subgroup = Group.objects.only('id').get(name=subgroup, service=subservice)
        except Group.DoesNotExist:
            raise GroupNotFound(subgroup)

        group.groups.add(subgroup)

    def set_subgroups(self, group, service, subgroups, subservice):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
            subgroups = [Group.objects.only('id').get(name=name, service=service)
                         for name in subgroups]
        except Group.DoesNotExist:
            raise GroupNotFound()

        pks = group.groups.filter(service=service).values_list('pk', flat=True)
        group.groups.remove(*pks)
        group.groups.add(*subgroups)

    def is_subgroup(self, group, service, subgroup, subservice):
        try:
            group = Group.objects.only('id').get(name=group, service=service)
        except Group.DoesNotExist:
            raise GroupNotFound(group)
        try:
            subgroup = Group.objects.only('id').get(name=subgroup, service=subservice)
        except Group.DoesNotExist:
            raise GroupNotFound(subgroup)

        return group.groups.filter(pk=subgroup.pk).exists()


class DjangoTransactionManagerOld(object):
    def __init__(self, backend, dry):
        self.backend = backend
        self.dry = dry

    def __enter__(self):
        return self.backend.init_transaction()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.dry or exc_type:
            self.backend.rollback_transaction()
        else:
            self.backend.commit_transaction()

    def __eq__(self, other):
        return isinstance(other, type(self))

    def __hash__(self):
        return hash(type(self))


class DjangoTransactionMixin(object):
    def init_transaction(self):
        dj_transaction.set_autocommit(False)

    def commit_transaction(self, transaction_id=None):
        dj_transaction.commit()
        dj_transaction.set_autocommit(True)

    def rollback_transaction(self, transaction_id=None):
        dj_transaction.rollback()
        dj_transaction.set_autocommit(True)

    def transaction_manager(self, dry=False):
        return DjangoTransactionManagerOld(self, dry=dry)


class DjangoGroupBackend(DjangoTransactionMixin, GroupBackend):
    """Use the standard Django ORM to store groups.

    This backend should be ready-to use as soon as you have :doc:`configured your database
    </config/database>`. This backend requires that you also use the
    :py:class:`~.DjangoUserBackend`.

    All settings used by this backend are documented in the :doc:`settings reference
    </config/all-config-values>`.
    """

    def get(self, name, service=None):
        try:
            return Group.objects.get(service=service, name=name)
        except Group.DoesNotExist:
            raise GroupNotFound(name)

    def subgroups(self, group, filter=True):
        if filter:
            qs = group.groups.filter(service=group.service)
            return list(qs.values_list('name', flat=True))
        else:
            return group.groups.all()

    def rm_subgroup(self, group, subgroup):
        qs = group.groups.filter(name=subgroup.name, service=subgroup.service)
        if not qs.exists():
            raise GroupNotFound(subgroup.name)

        group.groups.remove(subgroup)

    def remove(self, group):
        group.delete()

    def parents(self, group):
        return group.parent_groups.all()
