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

class UserBackend(object):
    def list(self):
        raise NotImplementedError

    def create(self, username, password=None, properties=None, dry=False):
        raise NotImplementedError

    def exists(self, username):
        raise NotImplementedError

    def check_password(self, username, password):
        raise NotImplementedError

    def set_password(self, username, password):
        raise NotImplementedError

    def remove(self, username):
        raise NotImplementedError


class PropertyBackend(object):
    def list(self, username):
        raise NotImplementedError

    def create(self, username, key, value, dry=False):
        raise NotImplementedError

    def get(self, username, key):
        raise NotImplementedError

    def set(self, username, key, value):
        raise NotImplementedError

    def set_multiple(self, username, props):
        raise NotImplementedError

    def remove(self, username, key):
        raise NotImplementedError


class GroupBackend(object):
    def list(self, username=None):
        raise NotImplementedError

    def create(self, service, groupname, dry=False):
        raise NotImplementedError

    def exists(self, service, groupname):
        raise NotImplementedError

    def add_user(self, service, groupname, username):
        raise NotImplementedError

    def members(self, service, groupname):
        raise NotImplementedError

    def is_member(self, service, groupname, username):
        raise NotImplementedError

    def rm_user(self, service, groupname, username):
        raise NotImplementedError

    def add_subgroup(self, service, groupname, subservice, subgroupname):
        raise NotImplementedError

    def subgroups(self, service, groupname, subservice):
        raise NotImplementedError

    def rm_subgroup(self, service, groupname, subservice, subgroupname):
        raise NotImplementedError

    def remove(self, service, groupname):
        raise NotImplementedError
