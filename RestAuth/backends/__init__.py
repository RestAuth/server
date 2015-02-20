# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from collections import deque

from django.conf import settings

from common.utils import import_path


def get_user_backend():
    return import_path(getattr(
        settings, 'USER_BACKEND',
        'backends.django_backend.DjangoUserBackend'
    ))[0]()


def get_property_backend():
    return import_path(getattr(
        settings, 'PROPERTY_BACKEND',
        'backends.django_backend.DjangoPropertyBackend'
    ))[0]()


def get_group_backend():
    return import_path(getattr(
        settings, 'GROUP_BACKEND',
        'backends.django_backend.DjangoGroupBackend'
    ))[0]()

user_backend = get_user_backend()
property_backend = get_property_backend()
group_backend = get_group_backend()


class transaction(object):
    """Context manager to ensure transaction-level consistency accross multiple backends.

    :param  users: Wether to enter a transaction for users.
    :type   users: bool
    :param  props: Wether to enter a transaction for properties.
    :type   props: bool
    :param groups: Wether to enter a transaction for groups.
    :type  groups: bool
    """

    def __init__(self, users=False, props=False, groups=False, dry=False):
        assert users or props or groups, "At least one of users, props, groups must be True."
        self.stack = deque()
        self.backends = set()

        if users is True:
            self.backends.add(user_backend.transaction_manager(dry=dry))
        if props is True:
            self.backends.add(property_backend.transaction_manager(dry=dry))
        if groups is True:
            self.backends.add(group_backend.transaction_manager(dry=dry))

    def __enter__(self):
        for backend in self.backends:
            backend.__enter__()
            self.stack.append(backend.__exit__)

    def __exit__(self, exc_type, exc_value, traceback):
        while self.stack:
            self.stack.pop()(exc_type, exc_value, traceback)


