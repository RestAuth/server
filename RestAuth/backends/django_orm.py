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
    def get(self, username):
        try:
            return User.objects.only('id', 'username').get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

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
        """
        :todo: The property arg should go to the property backend.
        """
        if dry:
            with transaction.commit_manually():
                try:
                    user = self._create(username, password, properties)
                    return user.username
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                user = self._create(username, password, properties)
                return user.username

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
    def list(self, user):
        return user.get_properties()

    def create(self, user, key, value, dry=False):
        if dry:
            with transaction.commit_manually():
                try:
                    prop = user.property_set.create(key=key, value=value)
                    return prop.key, prop.value
                except IntegrityError:
                    raise PropertyExists()
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                try:
                    prop = user.property_set.create(key=key, value=value)
                    return prop.key, prop.value
                except IntegrityError:
                    raise PropertyExists()

    def get(self, user, key):
        try:
            return user.property_set.get(key=key).value
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def set(self, user, key, value):
        prop, old_value = user.set_property(key, value)
        return prop.key, old_value

    def set_multiple(self, user, props):
        with transaction.commit_on_success():
            for key, value in props.iteritems():
                user.set_property(key, value)

    def remove(self, user, key):
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
                    group = Group.objects.create(
                        name=groupname, service=service)
                    return group.name
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % groupname)
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                try:
                    group = Group.objects.create(
                        name=groupname, service=service)
                    return group.name
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
