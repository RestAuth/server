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

import hashlib

import django
from django.conf import settings
from django.db import models
from django.utils.http import urlquote
from django.utils.encoding import smart_str

from RestAuth.common.utils import import_path

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

HASH_FUNCTION_CACHE = None


if django.get_version() >= '1.4':
    from django.utils.crypto import get_random_string
else:  # pragma: no cover
    from random import random

    def get_random_string(length=12):
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

    def set_password(self, raw_password):
        """Set the password to the given value."""
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

    def __unicode__(self):  # pragma: no cover
        return "%s: %s=%s" % (self.user.username, self.key, self.value)

    def get_absolute_url(self):
        userpath = self.user.get_absolute_url()
        return '%sprops/%s/' % (userpath, urlquote(self.key))
