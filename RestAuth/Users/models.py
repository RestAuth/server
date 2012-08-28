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

import django
from django.conf import settings
from django.db import models
from django.db.utils import IntegrityError
from django.utils.http import urlquote
from django.utils.encoding import smart_str

from RestAuthCommon import resource_validator
from RestAuthCommon.error import PreconditionFailed

from RestAuth.common.errors import PasswordInvalid
from RestAuth.common.errors import PropertyExists
from RestAuth.common.errors import UserExists
from RestAuth.common.errors import UsernameInvalid
from RestAuth.common.utils import import_path
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
USERNAME_VALIDATORS = None
USERNAME_ILLEGAL_CHARS = set()
USERNAME_RESERVED = set()
USERNAME_FORCE_ASCII = False
USERNAME_NO_WHITESPACE = False

HASH_FUNCTION_CACHE = None


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


def load_username_validators(validators=None):
    global USERNAME_VALIDATORS
    global USERNAME_ILLEGAL_CHARS
    global USERNAME_RESERVED
    global USERNAME_FORCE_ASCII
    global USERNAME_NO_WHITESPACE

    if validators is None:
        validators = settings.VALIDATORS

    USERNAME_VALIDATORS = []
    force_ascii = False
    allow_whitespace = True

    for validator_path in validators:
        validator = import_path(validator_path)[0]

        if hasattr(validator, 'check'):
            USERNAME_VALIDATORS.append(validator)

        USERNAME_ILLEGAL_CHARS |= validator.ILLEGAL_CHARACTERS
        USERNAME_RESERVED |= validator.RESERVED
        if validator.FORCE_ASCII:
            force_ascii = True
        if not validator.ALLOW_WHITESPACE:
            allow_whitespace = False

    USERNAME_FORCE_ASCII = force_ascii
    # use different regular expressions, depending on if we force ASCII
    if not allow_whitespace:
        if force_ascii:
            USERNAME_NO_WHITESPACE = re.compile('\s')
        else:
            USERNAME_NO_WHITESPACE = re.compile('\s', re.UNICODE)
    else:
        USERNAME_NO_WHITESPACE = False


def validate_username(username):
    if len(username) < settings.MIN_USERNAME_LENGTH:
        raise UsernameInvalid("Username too short")
    if len(username) > settings.MAX_USERNAME_LENGTH:
        raise UsernameInvalid("Username too long")

    if USERNAME_VALIDATORS is None:
        load_username_validators()

    # check for illegal characters:
    for char in USERNAME_ILLEGAL_CHARS:
        if char in username:
            raise UsernameInvalid(
                "Username must not contain character '%s'" % char)

    # reserved names
    if username in USERNAME_RESERVED:
        raise UsernameInvalid("Username is reserved")

    # force ascii if necessary
    if USERNAME_FORCE_ASCII:
        try:
            username.decode('ascii')
        except (UnicodeDecodeError, UnicodeEncodeError):
            raise UsernameInvalid(
                "Username must only contain ASCII characters")

    # check for whitespace
    if USERNAME_NO_WHITESPACE is not False:
        if USERNAME_NO_WHITESPACE.search(username):
            raise UsernameInvalid("Username must not contain any whitespace")

    for validator in USERNAME_VALIDATORS:
        validator.check(username)


if django.get_version() >= 1.4:
    from django.utils.crypto import get_random_string
else:
    def get_random_string(length=12):  # pragma: no cover
        """
        Get a very random salt. The salt is the first *length* characters of a
        sha512 hash of 5 random numbers concatenated.
        """
        random_string = ','.join(map(lambda a: str(random()), range(5)))
        return hashlib.sha512(random_string).hexdigest()[:length]


def load_hashers():
    global HASH_FUNCTION_CACHE

    cache = {}
    for path in settings.HASH_FUNCTIONS:
        func, name = import_path(path)
        cache[name] = func

    HASH_FUNCTION_CACHE = cache


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
        if HASH_FUNCTION_CACHE is None:
            load_hashers()

        hasher = HASH_FUNCTION_CACHE[algorithm]
        if salt is None:
            return hasher(secret, salt)
        else:
            return hasher(secret, smart_str(salt))


class ServiceUser(models.Model):
    username = models.CharField('username', max_length=60, unique=True)
    password = models.CharField('password', max_length=256,
                                blank=True, null=True)

    class Meta:
        permissions = user_permissions

    def __init__(self, *args, **kwargs):
        super(ServiceUser, self).__init__(*args, **kwargs)
        self.orig_username = self.username

    def save(self, *args, **kwargs):
        if self.pk is None or self.username != self.orig_username:
            if not resource_validator(self.username):
                raise PreconditionFailed(
                    "Username contains invalid characters")
        return super(ServiceUser, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        """
        Set the password to the given value. Throws PasswordInvalid if
        the password is shorter than settings.MIN_PASSWORD_LENGTH.

        @raise PasswordInvalid: When the password is too short.
        """
        if len(raw_password) < settings.MIN_PASSWORD_LENGTH:
            raise PasswordInvalid("Password too short")

        salt = get_random_string(16)
        digest = get_hexdigest(settings.HASH_ALGORITHM, salt, raw_password)
        self.password = '%s$%s$%s' % (settings.HASH_ALGORITHM, salt, digest)

    def set_unusable_password(self):
        self.password = None

    def check_password(self, raw_password):
        """
        Check the users password. If the current password hash is not
        of the same type as the current settings.HASH_ALGORITHM, the
        hash is updated but *not* saved.
        """
        if self.password is None:
            return False

        algo, salt, good_digest = self.password.split('$')
        digest = get_hexdigest(algo, salt, raw_password)
        if good_digest == digest:
            if algo != settings.HASH_ALGORITHM:
                self.set_password(raw_password)
                self.save()
            return True
        else:
            return False

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
