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

_user_backend = None
_property_backend = None
_group_backend = None

def load_user_backend():
    global _user_backend

    if _user_backend is None:
        _user_backend = import_path(getattr(
                settings, 'USER_BACKEND',
                'RestAuth.backends.django_backend.DjangoUserBackend'
        ))[0]()


def user_backend():
    if _user_backend is None:
        load_user_backend()

    return _user_backend


def load_property_backend():
    global _property_backend

    if _property_backend is None:
        _property_backend = import_path(getattr(
                settings, 'PROPERTY_BACKEND',
                'RestAuth.backends.django_backend.DjangoPropertyBackend'
        ))[0]()


def property_backend():
    if _property_backend is None:
        load_property_backend()

    return _property_backend


def load_group_backend():
    global _group_backend

    if _group_backend is None:
        _group_backend = import_path(getattr(
                settings, 'GROUP_BACKEND',
                'RestAuth.backends.django_backend.DjangoGroupBackend'
        ))[0]()

def group_backend():
    if _group_backend is None:
        load_group_backend()

    return _group_backend
