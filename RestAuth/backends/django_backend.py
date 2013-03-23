from datetime import datetime

from django.db import transaction as dj_transaction
from django.db.utils import IntegrityError

from RestAuth.Groups.models import Group
from RestAuth.Users.models import Property
from RestAuth.Users.models import ServiceUser as User
from RestAuth.backends.base import GroupBackend
from RestAuth.backends.base import PropertyBackend
from RestAuth.backends.base import UserBackend
from RestAuth.common.errors import GroupExists
from RestAuth.common.errors import GroupNotFound
from RestAuth.common.errors import PropertyExists
from RestAuth.common.errors import PropertyNotFound
from RestAuth.common.errors import UserExists
from RestAuth.common.errors import UserNotFound


class DjangoUserBackend(UserBackend):
    """Use the standard Django ORM to store user data.

    This backend should be ready-to use as soon as you have :doc:`configured
    your database </config/database>`.

    All settings used by this backend are documented in the :doc:`settings
    reference </config/all-config-values>`.
    """

    def _get_user(self, username, *fields):
        try:
            return User.objects.only(*fields).get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

    def get(self, username):
        return self._get_user(username, 'id', 'username')

    def list(self):
        return list(User.objects.values_list('username', flat=True))

    def _create(self, username, password=None, properties=None,
                property_backend=None, dry=False, transaction=True):
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

        property_backend.set_multiple(user, properties, dry=dry,
                                      transaction=transaction)
        return user

    def create(self, username, password=None, properties=None,
               property_backend=None, dry=False, transaction=True):
        if dry:
            with dj_transaction.commit_manually():
                try:
                    return self._create(username, password, properties,
                                        property_backend, dry=dry,
                                        transaction=transaction)
                finally:
                    dj_transaction.rollback()
        elif transaction:
            with dj_transaction.commit_on_success():
                return self._create(username, password, properties,
                                    property_backend, dry=dry,
                                    transaction=transaction)
        else:  # pragma: no cover
            return self._create(username, password, properties,
                                property_backend, dry=dry,
                                transaction=transaction)

    def exists(self, username):
        return User.objects.filter(username=username).exists()

    def check_password(self, username, password):
        user = self._get_user(username, 'password')
        return user.check_password(password)

    def set_password(self, username, password=None):
        user = self._get_user(username, 'id')
        if password is not None and password != '':
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()

    def set_password_hash(self, username, algorithm, hash, salt=None,
                          **kwargs):  # pragma: no cover
        user = self._get_user(username, 'password')
        parameters = [algorithm]
        if kwargs:
            parameters += kwargs.values()
        if salt is not None:
            parameters.append(salt)
        parameters.append(hash)

        user.password = '$'.join(parameters)
        user.save()

    def remove(self, username):
        qs = User.objects.filter(username=username)
        if qs.exists():
            qs.delete()
        else:
            raise UserNotFound(username)

    def init_transaction(self):  # pragma: no cover
        dj_transaction.enter_transaction_management()
        dj_transaction.managed(True)

    def commit_transaction(self):  # pragma: no cover
        dj_transaction.commit()

    def rollback_transaction(self):  # pragma: no cover
        dj_transaction.rollback()


class DjangoPropertyBackend(PropertyBackend):
    """Use the standard Django ORM to store user properties.

    This backend should be ready-to use as soon as you have :doc:`configured
    your database </config/database>`. This backend requires that you also use
    the :py:class:`~.DjangoUserBackend`.

    All settings used by this backend are documented in the :doc:`settings
    reference </config/all-config-values>`.
    """

    def list(self, user):
        qs = Property.objects.filter(user_id=user.id)
        return dict(qs.values_list('key', 'value'))

    def create(self, user, key, value, dry=False, transaction=True):
        if dry:
            with dj_transaction.commit_manually():
                try:
                    prop = user.property_set.create(key=key, value=value)
                    return prop.key, prop.value
                except IntegrityError:
                    raise PropertyExists()
                finally:
                    dj_transaction.rollback()
        elif transaction:
            with dj_transaction.commit_on_success():
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
        if dry:
            with dj_transaction.commit_manually():
                try:
                    prop, old_value = user.set_property(key, value)
                    return prop.key, old_value
                finally:
                    dj_transaction.rollback()
        elif transaction:
            with dj_transaction.commit_on_success():
                prop, old_value = user.set_property(key, value)
                return prop.key, old_value
        else:  # pragma: no cover
            prop, old_value = user.set_property(key, value)
            return prop.key, old_value

    def set_multiple(self, user, props, dry=False, transaction=True):
        if dry:
            with dj_transaction.commit_manually():
                try:
                    for key, value in props.items():
                        user.set_property(key, value)
                finally:
                    dj_transaction.rollback()
        elif transaction:
            with dj_transaction.commit_on_success():
                for key, value in props.items():
                    user.set_property(key, value)
        else:  # pragma: no cover
            for key, value in props.items():
                user.set_property(key, value)

    def remove(self, user, key):
        try:
            user.del_property(key)
        except Property.DoesNotExist:
            raise PropertyNotFound(key)

    def init_transaction(self):  # pragma: no cover
        dj_transaction.enter_transaction_management()
        dj_transaction.managed(True)

    def commit_transaction(self):  # pragma: no cover
        dj_transaction.commit()

    def rollback_transaction(self):  # pragma: no cover
        dj_transaction.rollback()


class DjangoGroupBackend(GroupBackend):
    """Use the standard Django ORM to store groups.

    This backend should be ready-to use as soon as you have :doc:`configured
    your database </config/database>`. This backend requires that you also use
    the :py:class:`~.DjangoUserBackend`.

    All settings used by this backend are documented in the :doc:`settings
    reference </config/all-config-values>`.
    """

    def get(self, name, service=None):
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

    def create(self, name, service=None, dry=False, transaction=True):
        if dry:
            with dj_transaction.commit_manually():
                try:
                    return Group.objects.create(
                        name=name, service=service)
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % name)
                finally:
                    dj_transaction.rollback()
        elif transaction:
            with dj_transaction.commit_on_success():
                try:
                    return Group.objects.create(
                        name=name, service=service)
                except IntegrityError:
                    raise GroupExists('Group "%s" already exists' % name)
        else:  # pragma: no cover
            try:
                return Group.objects.create(name=name, service=service)
            except IntegrityError:
                raise GroupExists('Group "%s" already exists' % name)

    def exists(self, name, service=None):
        return Group.objects.filter(name=name, service=service).exists()

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

    def init_transaction(self):  # pragma: no cover
        dj_transaction.enter_transaction_management()
        dj_transaction.managed(True)

    def commit_transaction(self):  # pragma: no cover
        dj_transaction.commit()

    def rollback_transaction(self):  # pragma: no cover
        dj_transaction.rollback()
