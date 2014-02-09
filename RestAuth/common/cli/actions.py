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

"""Collect various reusable parsers."""

from __future__ import unicode_literals

import string

from argparse import Action
from argparse import ArgumentError

from django.db.utils import IntegrityError
from django.utils import six

from RestAuthCommon import resource_validator

from Services.models import Service
from Services.models import ServiceUsernameNotValid
from Services.models import check_service_username
from Users.validators import validate_username
from backends import property_backend
from backends import user_backend
from common.errors import PreconditionFailed
from common.errors import UserExists
from common.errors import UserNotFound


PASSWORD_CHARS = string.digits + string.ascii_letters + string.punctuation
PASSWORD_CHARS = ''.join([c for c in PASSWORD_CHARS if c not in ['\\', '"', "'", '`']])


class ServiceAction(Action):
    def __call__(self, parser, namespace, value, option_string):
        if self.nargs == '?' and value is None:
            return

        if namespace.create_service:
            try:
                check_service_username(value)
                service = Service.objects.create(username=value)
            except IntegrityError:
                raise ArgumentError(self, 'Service already exists.')
            except ServiceUsernameNotValid as e:
                raise ArgumentError(self, e)
        else:
            try:
                service = Service.objects.get(username=value)
            except Service.DoesNotExist:
                raise ArgumentError(self, "Service does not exist.")

        setattr(namespace, self.dest, service)


class UsernameAction(Action):
    def __call__(self, parser, namespace, value, option_string):
        username = value.lower()
        if not six.PY3:  # pragma: no branch, pragma: py2
            username = username.decode('utf-8')

        if namespace.create_user:
            if not resource_validator(username):
                raise ArgumentError(self, "Username contains invalid characters")

            try:
                validate_username(username)
                user = user_backend.create(username=username, property_backend=property_backend)
            except UserExists:
                raise ArgumentError(self, 'User already exists.')
            except PreconditionFailed as e:
                raise ArgumentError(self, e)
        else:
            try:
                user = user_backend.get(username=username)
            except UserNotFound:
                raise ArgumentError(self, 'User does not exist.')
        setattr(namespace, self.dest, user)


class PasswordGeneratorAction(Action):
    def __call__(self, parser, namespace, values, option_string):
        passwd = Service.objects.make_random_password(length=16)
        setattr(namespace, 'password_generated', True)
        setattr(namespace, self.dest, passwd)
