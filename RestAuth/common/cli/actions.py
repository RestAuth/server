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

from argparse import Action, ArgumentError
import random
import string

from django.db.utils import IntegrityError

from RestAuth.Services.models import Service
from RestAuth.Services.models import check_service_username
from RestAuth.Services.models import ServiceUsernameNotValid
from RestAuth.Users.models import ServiceUser as User
from RestAuth.common.errors import PreconditionFailed


class ServiceAction(Action):
    def __call__(self, parser, namespace, value, option_string):
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
        username = value.lower().decode('utf-8')
        if namespace.create_user:
            try:
                user = User.objects.create(username=username)
            except IntegrityError:
                raise ArgumentError(self, 'User already exists.')
            except PreconditionFailed as e:
                raise ArgumentError(self, e)
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise ArgumentError(self, 'User does not exist.')
        setattr(namespace, self.dest, user)


class PasswordGeneratorAction(Action):
    def __call__(self, parser, namespace, values, option_string):
        chars = string.digits + string.letters + string.punctuation
        chars = chars.translate(None, '\\\'"`')

        passwd = ''.join(random.choice(chars) for x in range(30))
        setattr(namespace, 'password_generated', True)
        setattr(namespace, self.dest, passwd)