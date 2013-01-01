from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError

from RestAuth.backends.base import GroupBackend
from RestAuth.backends.base import PropertyBackend
from RestAuth.backends.base import UserBackend
from RestAuth.common.errors import UserExists, GroupExists, PropertyExists
from RestAuth.common.errors import UserNotFound, PropertyNotFound
from RestAuth.common.errors import GroupNotFound
from RestAuth.common.utils import import_path

from RestAuth.Users.models import ServiceUser as User, Property
from RestAuth.Groups.models import Group


class DjangoBackendBase(object):
    pass


class DjangoUserBackend(UserBackend, DjangoBackendBase):
    def _get_user(self, username, *fields):
        try:
            return User.objects.only(*fields).get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def get(self, username):
        return self._get_user(username, 'id', 'username')

    def list(self):
        return list(User.objects.values_list('username', flat=True))

    def _create(self, username, password=None, properties=None, dry=False):
        try:
            user = User(username=username)
            if password is not None and password != '':
                user.set_password(password)
            user.save()
        except IntegrityError:
            raise UserExists("A user with the given name already exists.")

        if properties is None:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            properties = {'date joined': stamp}
        elif 'date joined' not in properties:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            properties['date joined'] = stamp

        self._get_property_backend().set_multiple(user, properties, dry=dry)
        return user

    def create(self, username, password=None, properties=None, dry=False):
        if dry:
            with transaction.commit_manually():
                try:
                    return self._create(username, password, properties,
                                        dry=dry)
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                return self._create(username, password, properties, dry=dry)

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
        qs = Property.objects.filter(user_id=user.id)
        return dict(qs.values_list('key', 'value'))

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
            qs = Property.objects.filter(user_id=user.id).only('value')
            return qs.get(key=key).value
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def set(self, user, key, value):
        prop, old_value = user.set_property(key, value)
        return prop.key, old_value

    def set_multiple(self, user, props, dry=False):
        if dry:
            with transaction.commit_manually():
                try:
                    for key, value in props.iteritems():
                        user.set_property(key, value)
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                for key, value in props.iteritems():
                    user.set_property(key, value)

    def remove(self, user, key):
        try:
            user.del_property(key)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)


class DjangoGroupBackend(GroupBackend, DjangoBackendBase):
    def get(self, service, name):
        try:
            return Group.objects.get(service=service, name=name)
        except Group.DoesNotExist:
            raise GroupNotFound(name)

    def list(self, service, user=None):
        if user is None:
            groups = Group.objects.filter(service=service)
        else:
            groups = Group.objects.member(user=user, service=service)
        return list(groups.only('id').values_list('name', flat=True))

    def create(self, service, name, dry=False):
        if dry:
            with transaction.commit_manually():
                try:
                    return Group.objects.create(
                        name=name, service=service)
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % name)
                finally:
                    transaction.rollback()
        else:
            with transaction.commit_on_success():
                try:
                    return Group.objects.create(
                        name=name, service=service)
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % name)

    def exists(self, service, groupname):
        return Group.objects.filter(name=groupname, service=service).exists()

    def add_user(self, group, user):
        group.users.add(user)

    def members(self, group, depth=None):
        qs = group.get_members(depth=depth)
        return list(qs.values_list('username', flat=True))

    def is_member(self, group, user):
        if group.is_member(user):
            return True
        return False

    def rm_user(self, group, user):
        if group.is_member(user):
            group.users.remove(user)
        else:
            raise UserNotFound(user)  # 404 Not Found

    def add_subgroup(self, group, subgroup):
        group.groups.add(subgroup)

    def subgroups(self, group, filter=True):
        qs = group.groups
        if filter:
            qs = qs.filter(service=group.service)
        return list(qs.values_list('name', flat=True))

    def rm_subgroup(self, group, subgroup):
        qs = group.groups.filter(name=subgroup.name, service=subgroup.service)
        if not qs.exists():
            raise GroupNotFound(subgroup.name)

        group.groups.remove(subgroup)

    def remove(self, service, groupname):
        if not Group.objects.filter(name=groupname, service=service).exists():
            raise GroupNotFound(groupname)
        Group.objects.filter(name=groupname, service=service).delete()

    def parents(self, group):
        return list(group.parent_groups.all().values_list('name', flat=True))
