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

from __future__ import unicode_literals

from django.contrib.auth.models import User as BaseUser
from django.db import transaction as dj_transaction
from django.db.utils import IntegrityError
from django.utils import six

from Groups.models import Group
from Users.models import Property
from Users.models import ServiceUser as User
from backends.base import GroupBackend
from backends.base import PropertyBackend
from backends.base import UserBackend
from common.hashers import import_hash
from common.errors import GroupExists
from common.errors import GroupNotFound
from common.errors import PropertyExists
from common.errors import PropertyNotFound
from common.errors import UserExists
from common.errors import UserNotFound


class DjangoTransactionManager(object):
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
        return DjangoTransactionManager(self, dry=dry)


class DjangoUserBackend(DjangoTransactionMixin, UserBackend):
    """Use the standard Django ORM to store user data.

    This backend should be ready-to use as soon as you have :doc:`configured your database
    </config/database>`.

    All settings used by this backend are documented in the :doc:`settings reference
    </config/all-config-values>`.
    """

    def _get_user(self, username, *fields):
        assert isinstance(username, six.string_types)

        try:
            return User.objects.only(*fields).get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def get(self, username):
        assert isinstance(username, six.string_types)
        return self._get_user(username, 'id', 'username')

    def list(self):
        return list(User.objects.values_list('username', flat=True))

    def _create(self, username, password=None, dry=False, transaction=True):
        assert isinstance(username, six.string_types)
        assert isinstance(password, six.string_types) or password is None

        try:
            user = User(username=username)
            if password is not None and password != '':
                user.set_password(password)
            user.save()
        except IntegrityError:
            raise UserExists("A user with the given name already exists.")

        return user

    def create(self, username, password=None, dry=False, transaction=True):
        assert isinstance(username, six.string_types)
        assert isinstance(password, six.string_types) or password is None

        if dry:
            dj_transaction.set_autocommit(False)

            try:
                return self._create(username, password, dry=dry,
                                    transaction=transaction)
            finally:
                dj_transaction.rollback()
                dj_transaction.set_autocommit(True)
        elif transaction:
            with dj_transaction.atomic():
                return self._create(username, password, dry=dry, transaction=transaction)
        else:
            return self._create(username, password, dry=dry, transaction=transaction)

    def rename(self, username, name):
        assert isinstance(username, six.string_types)
        assert isinstance(name, six.string_types)

        user = self._get_user(username)

        user.username = name
        try:
            user.save()
        except IntegrityError:
            raise UserExists("User already exists.")

    def exists(self, username):
        assert isinstance(username, six.string_types)
        return User.objects.filter(username=username).exists()

    def check_password(self, username, password):
        assert isinstance(username, six.string_types)
        assert isinstance(password, six.string_types)

        user = self._get_user(username, 'password')
        return user.check_password(password)

    def set_password(self, username, password=None):
        assert isinstance(username, six.string_types)
        assert isinstance(password, six.string_types) or password is None

        user = self._get_user(username, 'id')
        if password is not None and password != '':
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

    def set_password_hash(self, username, algorithm, hash):
        assert isinstance(username, six.string_types)
        assert isinstance(algorithm, six.string_types)
        assert isinstance(hash, six.string_types)

        user = self._get_user(username, 'password')

        user.password = import_hash(algorithm=algorithm, hash=hash)
        user.save()

    def remove(self, username):
        assert isinstance(username, six.string_types)

        qs = User.objects.filter(username=username)
        if qs.exists():
            qs.delete()
        else:
            raise UserNotFound(username)


class DjangoPropertyBackend(DjangoTransactionMixin, PropertyBackend):
    """Use the standard Django ORM to store user properties.

    This backend should be ready-to use as soon as you have :doc:`configured your database
    </config/database>`. This backend requires that you also use the
    :py:class:`~.DjangoUserBackend`.

    All settings used by this backend are documented in the :doc:`settings reference
    </config/all-config-values>`.
    """

    def list(self, user):
        qs = Property.objects.filter(user_id=user.id)
        return dict(qs.values_list('key', 'value'))

    def create(self, user, key, value, dry=False, transaction=True):
        if dry:
            dj_transaction.set_autocommit(False)

            try:
                prop = user.property_set.create(key=key, value=value)
                return prop.key, prop.value
            except IntegrityError:
                raise PropertyExists()
            finally:
                dj_transaction.rollback()
                dj_transaction.set_autocommit(True)
        elif transaction:
            with dj_transaction.atomic():
                try:
                    prop = user.property_set.create(key=key, value=value)
                    return prop.key, prop.value
                except IntegrityError:
                    raise PropertyExists()
        else:  # pragma: no cover
            try:
                prop = user.property_set.create(key=key, value=value)
                return prop.key, prop.value
            except IntegrityError:
                raise PropertyExists()

    def get(self, user, key):
        try:
            qs = Property.objects.filter(user_id=user.id).only('value')
            return qs.get(key=key).value
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def set(self, user, key, value, dry=False, transaction=True):
        # we do not need the dry parameter if its not set by set_multiple.
        if transaction:
            with dj_transaction.atomic():
                prop, old_value = user.set_property(key, value)
                return prop.key, old_value
        else:  # pragma: no cover
            prop, old_value = user.set_property(key, value)
            return prop.key, old_value

    def set_multiple(self, user, props, dry=False, transaction=True):
        if dry:
            dj_transaction.set_autocommit(False)

            try:
                for key, value in six.iteritems(props):
                    user.set_property(key, value)
            finally:
                dj_transaction.rollback()
                dj_transaction.set_autocommit(True)
        elif transaction:
            with dj_transaction.atomic():
                for key, value in six.iteritems(props):
                    user.set_property(key, value)
        else:  # pragma: no cover
            for key, value in six.iteritems(props):
                user.set_property(key, value)

    def remove(self, user, key):
        try:
            user.del_property(key)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)


class DjangoGroupBackend(DjangoTransactionMixin, GroupBackend):
    """Use the standard Django ORM to store groups.

    This backend should be ready-to use as soon as you have :doc:`configured your database
    </config/database>`. This backend requires that you also use the
    :py:class:`~.DjangoUserBackend`.

    All settings used by this backend are documented in the :doc:`settings reference
    </config/all-config-values>`.
    """

    def get(self, name, service=None):
        assert isinstance(name, six.string_types)
        assert isinstance(service, BaseUser) or service is None

        try:
            return Group.objects.get(service=service, name=name)
        except Group.DoesNotExist:
            raise GroupNotFound(name)

    def list(self, service=None, user=None):
        assert isinstance(service, BaseUser) or service is None
        assert isinstance(user, User) or user is None

        if user is None:
            groups = Group.objects.filter(service=service)
        else:
            groups = Group.objects.member(user=user, service=service)
        return list(groups.only('id').values_list('name', flat=True))

    def create(self, name, service=None, users=None, dry=False, transaction=True):
        assert isinstance(service, BaseUser) or service is None
        assert isinstance(name, six.string_types)

        if dry:
            dj_transaction.set_autocommit(False)

            try:
                group = Group.objects.create(name=name, service=service)
                if users:
                    group.users.add(*users)
                return group
            except IntegrityError:
                raise GroupExists('Group "%s" already exists' % name)
            finally:
                dj_transaction.rollback()
                dj_transaction.set_autocommit(True)
        elif transaction:
            with dj_transaction.atomic():
                try:
                    group = Group.objects.create(name=name, service=service)
                    if users:
                        group.users.add(*users)
                    return group
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % name)
        else:  # pragma: no cover
            try:
                group = Group.objects.create(name=name, service=service)
                if users:
                    group.users.add(*users)
                return group
            except IntegrityError:
                raise GroupExists('Group "%s" already exists' % name)

    def rename(self, group, name):
        assert isinstance(group, Group)
        assert isinstance(name, six.string_types)

        try:
            group.name = name
            group.save()
        except IntegrityError:
            raise GroupExists("Group already exists.")

    def set_service(self, group, service=None):
        assert isinstance(group, Group)
        assert isinstance(service, BaseUser) or service is None, type(service)

        group.service = service
        group.save()

    def exists(self, name, service=None):
        assert isinstance(service, BaseUser) or service is None
        assert isinstance(name, six.string_types)

        return Group.objects.filter(name=name, service=service).exists()

    def set_groups_for_user(self, service, user, groupnames, transaction=True, dry=False):
        user.group_set.filter(service=service).delete()  # clear existing groups
        groups = []
        for name in groupnames:
            try:
                groups.append(Group.objects.get(service=service, name=name))
            except Group.DoesNotExist:
                groups.append(Group.objects.create(service=service, name=name))
        user.group_set.add(*groups)

    def set_users_for_group(self, group, users):
        group.users.clear()
        group.users.add(*users)

    def add_user(self, group, user):
        assert isinstance(group, Group)
        assert isinstance(user, User)

        group.users.add(user)

    def members(self, group, depth=None):
        assert isinstance(group, Group)

        qs = group.get_members(depth=depth)
        return list(qs.values_list('username', flat=True))

    def is_member(self, group, user):
        assert isinstance(group, Group)
        assert isinstance(user, User)

        if group.is_member(user):
            return True
        return False

    def rm_user(self, group, user):
        assert isinstance(group, Group)
        assert isinstance(user, User)

        if group.is_member(user):
            group.users.remove(user)
        else:
            raise UserNotFound(user)  # 404 Not Found

    def add_subgroup(self, group, subgroup):
        assert isinstance(group, Group)
        assert isinstance(subgroup, Group)

        group.groups.add(subgroup)

    def subgroups(self, group, filter=True):
        assert isinstance(group, Group)

        if filter:
            qs = group.groups.filter(service=group.service)
            return list(qs.values_list('name', flat=True))
        else:
            return group.groups.all()

    def rm_subgroup(self, group, subgroup):
        assert isinstance(group, Group)
        assert isinstance(subgroup, Group)

        qs = group.groups.filter(name=subgroup.name, service=subgroup.service)
        if not qs.exists():
            raise GroupNotFound(subgroup.name)

        group.groups.remove(subgroup)

    def remove(self, group):
        assert isinstance(group, Group)
        group.delete()

    def parents(self, group):
        assert isinstance(group, Group)
        return group.parent_groups.all()
