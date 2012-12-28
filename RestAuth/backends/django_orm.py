from datetime import datetime

from django.db import transaction
from django.db.utils import IntegrityError

from RestAuth.backends.base import GroupBackend
from RestAuth.backends.base import PropertyBackend
from RestAuth.backends.base import UserBackend
from RestAuth.common.errors import UserExists, GroupExists, PropertyExists
from RestAuth.common.errors import UserNotFound, PropertyNotFound
from RestAuth.common.errors import GroupNotFound

from RestAuth.Users.models import ServiceUser as User, Property
from RestAuth.Groups.models import Group


class DjangoBackendBase(object):
    def _get_user(self, username, *fields):
        try:
            return User.objects.only(*fields).get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def _get_group(self, service, name, *fields):
        try:
            return Group.objects.only(*fields).get(service=service, name=name)
        except Group.DoesNotExist:
            raise GroupNotFound(name)

class DjangoUserBackend(UserBackend, DjangoBackendBase):
    def list(self):
        return list(User.objects.values_list('username', flat=True))

    def _create(self, username, password=None, properties=None):
        try:
            user = User(username=username)
            if password is not None and password != '':
                user.set_password(password)
            user.save()
        except IntegrityError:
            raise UserExists("A user with the given name already exists.")

        if properties is not None:
            for key, value in properties.iteritems():
                user.set_property(key, value)

        if properties is None or 'date joined' not in properties:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user.set_property('date joined', stamp)
        return user

    def create(self, username, password=None, properties=None, dry=False):
        if dry:
            with transaction.commit_manually():
                try:
                    user = self._create(username, password, properties)
                    return user
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                return self._create(username, password, properties)

    def check_password(self, username, password):
        user = self._get_user(username, 'password')
        return user.check_password(password)

    def exists(self, username):
        return User.objects.filter(username=username).exists()

    def set_password(self, username, password):
        user = self._get_user(username, 'id')
        if password is not None and password != '':
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

    def remove(self, username):
        qs = User.objects.filter(username=username)
        if qs.exists():
            qs.delete()
        else:
            raise UserNotFound(username)


class DjangoPropertyBackend(PropertyBackend, DjangoBackendBase):
    def list(self, username):
        user = self._get_user(username, 'id')
        return user.get_properties()

    def create(self, username, key, value, dry=False):
        user = self._get_user(username, 'id')

        if dry:
            with transaction.commit_manually():
                try:
                    return user.add_property(key, value)
                except IntegrityError:
                    raise PropertyExists()
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                try:
                    return user.add_property(key, value)
                except IntegrityError:
                    raise PropertyExists()

    def get(self, username, key):
        user = self._get_user(username, 'id')
        try:
            return user.get_property(key).value
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def set(self, username, key, value):
        user = self._get_user(username, 'id')
        return user.set_property(key, value)

    def set_multiple(self, username, props):
        user = self._get_user(username, 'id')
        with transaction.commit_on_success():
            for key, value in props.iteritems():
                user.set_property(key, value)

    def remove(self, username, key):
        user = self._get_user(username, 'id')
        try:
            user.del_property(key)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)


class DjangoGroupBackend(GroupBackend, DjangoBackendBase):
    def list(self, service, username=None):
        if username is None:
            groups = Group.objects.filter(service=service)
        else:
            user = self._get_user(username, 'id')

            groups = Group.objects.member(user=user, service=service)
        return list(groups.only('id').values_list('name', flat=True))

    def create(self, service, groupname, dry=False):
        if dry:
            with transaction.commit_manually():
                try:
                    return Group.objects.create(
                        name=groupname, service=service)
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % groupname)
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                try:
                    return Group.objects.create(
                        name=groupname, service=service)
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % groupname)

    def exists(self, service, groupname):
        return Group.objects.filter(name=groupname, service=service).exists()

    def add_user(self, service, groupname, username):
        group = self._get_group(service, groupname, 'id')
        user = self._get_user(username, 'id')
        group.users.add(user)

    def members(self, service, groupname):
        group = self._get_group(service, groupname, 'id')
        return list(group.get_members().values_list('username', flat=True))

    def is_member(self, service, groupname, username):
        group = self._get_group(service, groupname, 'id')
        if group.is_member(username):
            return True
        return False

    def rm_user(self, service, groupname, username):
        group = self._get_group(service, groupname, 'id')
        user = self._get_user(username, 'id')

        if group.is_member(username):
            group.users.remove(user)
        else:
            raise UserNotFound(username)  # 404 Not Found

    def add_subgroup(self, service, groupname, subservice, subgroupname):
        group = self._get_group(service, groupname, 'id')
        subgroup = self._get_group(subservice, subgroupname, 'id')
        group.groups.add(subgroup)

    def subgroups(self, service, groupname):
        group = self._get_group(service, groupname, 'id')
        groups = group.groups.filter(service=service)
        return list(groups.values_list('name', flat=True))

    def rm_subgroup(self, service, groupname, subservice, subgroupname):
        group = self._get_group(service, groupname, 'id')
        subgroup = self._get_group(subservice, subgroupname, 'id')

        qs = group.groups.filter(name=subgroupname, service=subservice)
        if not qs.exists():
            raise GroupNotFound(subgroupname)

        group.groups.remove(subgroup)

    def remove(self, service, groupname):
        if not Group.objects.filter(name=groupname, service=service).exists():
            raise GroupNotFound(groupname)
        Group.objects.filter(name=groupname, service=service).delete()
