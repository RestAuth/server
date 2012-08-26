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

import datetime
import hashlib
from random import random
import re
import stringprep

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.utils import IntegrityError
from django.utils.http import urlquote
from django.utils.importlib import import_module
from django.utils.encoding import smart_str

from RestAuthCommon.error import PreconditionFailed
from RestAuthCommon import resource_validator

from RestAuth.common.errors import PasswordInvalid
from RestAuth.common.errors import PropertyExists
from RestAuth.common.errors import UserExists
from RestAuth.common.errors import UsernameInvalid
from RestAuth.Users import validators

user_permissions = (
    ('users_list', 'List all users'),
    ('user_create', 'Create a new user'),
    ('user_exists', 'Check if a user exists'),
    ('user_delete', 'Delete a user'),
    ('user_verify_password', 'Verify a users password'),
    ('user_change_password', 'Change a users password'),
    ('user_delete_password', 'Delete a user'),
)
prop_permissions = (
    ('props_list', 'List all properties of a user'),
    ('prop_create', 'Create a new property'),
    ('prop_get', 'Get value of a property'),
    ('prop_set', 'Set or create a property'),
    ('prop_delete', 'Delete a property'),
)


def user_get(name):
    """
    Get a user with the given username.

    Note: this is only used by the CLI interface any more.

    @raises ServiceUser.DoesNotExist: When the user does not exist.
    """
    return ServiceUser.objects.get(username=name.lower())


def user_create(name, password):
    """
    Creates a new user. Lowercases the username.

    @raise UserExists: If the user already exists
    @raise UsernameInvalid: If the username is unacceptable
    @raise PasswordInvalid: If the password is unacceptable
    """
    name = name.lower()
    validate_username(name)
    try:
        user = ServiceUser(username=name)
        if password:
            user.set_password(password)
        user.save()
        return user
    except IntegrityError:
        raise UserExists("A user with the given name already exists.")


def validate_username(username):
    if len(username) < settings.MIN_USERNAME_LENGTH:
        raise UsernameInvalid("Username too short")
    if len(username) > settings.MAX_USERNAME_LENGTH:
        raise UsernameInvalid("Username too long")

    illegal_chars = set()
    reserved = set()
    force_ascii = False
    allow_whitespace = True
    validators = []

    for validator_path in settings.VALIDATORS:
        # import validator:
        try:
            modname, classname = validator_path.rsplit('.', 1)
        except ValueError:
            raise ImproperlyConfigured(
                '%s isn\'t a middleware module' % validator_path)

        try:
            mod = import_module(modname)
        except ImportError as e:
            raise ImproperlyConfigured(
                'Error importing middleware %s: "%s"' % (modname, e))
        try:
            validator = getattr(mod, classname)
        except AttributeError:
            msg = 'Middleware module "%s" does not define a "%s" class'
            raise ImproperlyConfigured(msg % (modname, classname))

        if hasattr(validator, 'check'):
            validators.append(validator)

        illegal_chars |= validator.ILLEGAL_CHARACTERS
        reserved |= validator.RESERVED
        if validator.FORCE_ASCII:
            force_ascii = True
        if not validator.ALLOW_WHITESPACE:
            allow_whitespace = False

    # check for illegal characters:
    for char in illegal_chars:
        if char in username:
            raise UsernameInvalid(
                "Username must not contain character '%s'" % char)

    # reserved names
    if username in reserved:
        raise UsernameInvalid("Username is reserved")

    # force ascii if necessary
    if force_ascii:
        try:
            username.decode('ascii')
        except UnicodeDecodeError:
            raise UsernameInvalid(
                "Username must only contain ASCII characters")

    # check for whitespace
    if not allow_whitespace:
        if force_ascii:
            whitespace_regex = re.compile('\s')
        else:
            whitespace_regex = re.compile('\s', re.UNICODE)
        if whitespace_regex.search(username):
            raise UsernameInvalid("Username must not contain any whitespace")

    for validator in validators:
        validator.check(username)


def get_salt():
    """
    Get a very random salt. The salt is the first eight characters of a
    sha512 hash of 5 random numbers concatenated.
    """
    random_string = ','.join(map(lambda a: str(random()), range(5)))
    return hashlib.sha512(random_string).hexdigest()[:8]


def get_hexdigest(algorithm, salt=None, secret=''):
    """
    This method overrides the standard get_hexdigest method for service
    users. It adds support for for the 'mediawiki' hash-type and any
    crypto-algorithm included in the hashlib module.
    """
    secret = smart_str(secret)

    if hasattr(hashlib, algorithm):
        func = getattr(hashlib, algorithm)
        if salt is None:
            return func(secret).hexdigest()
        else:
            return func('%s%s' % (smart_str(salt), secret)).hexdigest()
    else:
        for path in settings.HASH_FUNCTIONS:
            # import validator:
            try:
                modname, funcname = path.rsplit('.', 1)
            except ValueError:  # pragma: no cover
                raise ImproperlyConfigured('%s isn\'t a python path' % path)

            # skip if funcname is not the desired algorithm:
            if algorithm != funcname:
                continue

            try:
                mod = import_module(modname)
            except ImportError as e:  # pragma: no cover
                raise ImproperlyConfigured(
                    'Error importing module %s: "%s"' % (modname, e))
            try:
                func = getattr(mod, funcname)
            except AttributeError:  # pragma: no cover
                msg = 'Module "%s" does not define a "%s" function'
                raise ImproperlyConfigured(msg % (modname, funcname))

            if salt is None:
                return func(secret, salt)
            else:
                return func(secret, smart_str(salt))


class ServiceUser(models.Model):
    username = models.CharField('username', max_length=60, unique=True)
    password = models.CharField('password', max_length=256,
                                blank=True, null=True)
    last_login = models.DateTimeField('last login',
                                      auto_now=True, auto_now_add=True)
    date_joined = models.DateTimeField('date joined', auto_now_add=True)

    class Meta:
        permissions = user_permissions

    def __init__(self, *args, **kwargs):
        super(ServiceUser, self).__init__(*args, **kwargs)
        self.orig_username = self.username

    def save(self, *args, **kwargs):
        if self.pk is None or self.username != self.orig_username:
            if not resource_validator(self.username):
                raise PreconditionFailed("Username contains invalid characters")
        return super(ServiceUser, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        """
        Set the password to the given value. Throws PasswordInvalid if
        the password is shorter than settings.MIN_PASSWORD_LENGTH.

        @raise PasswordInvalid: When the password is too short.
        """
        if len(raw_password) < settings.MIN_PASSWORD_LENGTH:
            raise PasswordInvalid("Password too short")

        salt = get_salt()
        hash = get_hexdigest(settings.HASH_ALGORITHM, salt, raw_password)
        self.password = '%s$%s%s' % (algo, salt, hash)

    def set_unusable_password(self):
        self.password = None

    def check_password(self, raw_password):
        """
        Check the users password. If the current password hash is not
        of the same type as the current settings.HASH_ALGORITHM, the
        hash is updated but *not* saved.
        """
        if not (self.algorithm and self.hash):
            return False

        digest = get_hexdigest(self.algorithm, self.salt, raw_password)
        if digest == self.hash:  # correct
            if self.algorithm != settings.HASH_ALGORITHM:  # pragma: no cover
                # we do this manually so we avoid any checks.
                self.algorithm = settings.HASH_ALGORITHM
                self.salt = get_salt()
                self.hash = get_hexdigest(
                    self.algorithm, self.salt, raw_password)
            return True
        else:  # password not correct
            return False

    def get_groups(self, service):
        """
        Get a list of groups that this user is a member of.

        @param service: Limit the list of groups to those defined by the
            given service.
        @type  service: service
        """
        groups = set(self.group_set.filter(service=service).only('name'))
        model = self.group_set.model

        # any remaining candidates
        exclude_ids = [group.id for group in groups]
        others = model.objects.filter(service=service).exclude(
            id__in=exclude_ids).only('name')
        for other in others:
            if other.is_indirect_member(self):
                groups.add(other)
        return groups

    def add_property(self, key, value):
        """
        Add a new property to this user. It is an error if this property
        already exists.

        @raises PropertyExists: If the property already exists.
        @return: The property that was created
        """
        try:
            return Property.objects.create(user=self, key=key, value=value)
        except IntegrityError:
            raise PropertyExists(key)

    def get_properties(self):
        return dict(self.property_set.values_list('key', 'value').all())

    def set_property(self, key, value):
        """
        Set the property identified by I{key} to I{value}. If the
        property already exists, it is overwritten.

        @return: Returns a tuple. The first value represents the
            L{Property} acted upon and the second value is a string
            with the previous value or None if this was a new
            property.
        """
        prop, created = Property.objects.get_or_create(
            user=self, key=key, defaults={'value': value})
        if created:
            return prop, None
        else:
            old_value = prop.value
            prop.value = value
            prop.save()
            return prop, old_value

    def get_property(self, key):
        """
        Get value of a specific property.

        @raises Property.DoesNotExist: When the property does not exist.
        """
        # exactly one SELECT statement
        return self.property_set.get(key=key)

    def del_property(self, key):
        """
        Delete a property.

        @raises Property.DoesNotExist: When the property does not exist.
        """
        if self.property_set.filter(key=key).exists():
            self.property_set.filter(key=key).delete()
        else:
            raise Property.DoesNotExist()

    def __unicode__(self):  # pragma: no cover
        return self.username

    def get_absolute_url(self):
        return '/users/%s/' % urlquote(self.username)


class Property(models.Model):
    user = models.ForeignKey(ServiceUser)
    key = models.CharField(max_length=128, db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ('user', 'key')
        permissions = prop_permissions

    def save(self, *args, **kwargs):
        if self.pk is None and not resource_validator(self.key):
            raise PreconditionFailed("Property contains invalid characters")
        return super(Property, self).save(*args, **kwargs)

    def __unicode__(self):  # pragma: no cover
        return "%s: %s=%s" % (self.user.username, self.key, self.value)

    def get_absolute_url(self):
        userpath = self.user.get_absolute_url()
        return '%sprops/%s/' % (userpath, urlquote(self.key))
