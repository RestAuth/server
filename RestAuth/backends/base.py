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

from django.conf import settings

from RestAuth.common.utils import import_path


class UserBackend(object):
    property_backend = None

    @classmethod
    def _get_property_backend(cls):
        if cls.property_backend is None:
            cls.property_backend = import_path(getattr(
                settings, 'PROPERTY_BACKEND',
                'RestAuth.backends.django_orm.DjangoPropertyBackend'
            ))[0]()

        return cls.property_backend

    def get(self, username):
        raise NotImplementedError

    def list(self):
        raise NotImplementedError

    def create(self, username, password=None, properties=None,
               property_backend=None, dry=False):
        raise NotImplementedError

    def exists(self, username):
        raise NotImplementedError

    def check_password(self, username, password):
        raise NotImplementedError

    def set_password(self, username, password):
        raise NotImplementedError

    def remove(self, username):
        raise NotImplementedError

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass


class PropertyBackend(object):
    def list(self, user):
        raise NotImplementedError

    def create(self, user, key, value, dry=False):
        raise NotImplementedError

    def get(self, user, key):
        raise NotImplementedError

    def set(self, user, key, value):
        raise NotImplementedError

    def set_multiple(self, user, props, dry=False):
        raise NotImplementedError

    def remove(self, user, key):
        raise NotImplementedError

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass


class GroupBackend(object):
    def get(self, service, name):
        raise NotImplementedError

    def list(self, service, user=None):
        raise NotImplementedError

    def create(self, service, name, dry=False):
        raise NotImplementedError

    def exists(self, service, name):
        raise NotImplementedError

    def add_user(self, user, group):
        raise NotImplementedError

    def members(self, group, depth=None):
        raise NotImplementedError

    def is_member(self, group, user):
        raise NotImplementedError

    def rm_user(self, group, user):
        raise NotImplementedError

    def add_subgroup(self, group, subgroup):
        raise NotImplementedError

    def subgroups(self, group, filter=True):
        raise NotImplementedError

    def rm_subgroup(self, group, subgroup):
        raise NotImplementedError

    def remove(self, group):
        raise NotImplementedError

    def parents(self, group):
        raise NotImplementedError

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass
