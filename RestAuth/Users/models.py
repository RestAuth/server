# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.db import models


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


class ServiceUser(models.Model):
    username = models.CharField('username', max_length=60, unique=True)
    password = models.CharField('password', max_length=256, blank=True, null=True)

    class Meta:
        permissions = user_permissions

    def set_password(self, raw_password):
        """Set the password to the given value."""
        self.password = make_password(raw_password)

    def set_unusable_password(self):
        """Set an unusable password."""
        self.password = make_password(None)

    def check_password(self, raw_password):
        """Check a users password."""
        def setter(raw_password):
            self.set_password(raw_password)
            self.save()
        return check_password(raw_password, self.password, setter)

    def set_property(self, key, value):
        """Set the property identified by I{key} to I{value}. If the property already exists, it is
        overwritten.

        :return: Returns a tuple. The first value represents the L{Property} acted upon and the
                 second value is a string with the previous value or None if this was a new
                 property.
        """
        # WARNING: do not use get_or_create here, as that method has an atomic() block.
        try:
            prop = Property.objects.get(user=self, key=key)
            old_value = prop.value
            prop.value = value
            prop.save()
            return prop, old_value
        except Property.DoesNotExist:
            return Property.objects.create(user=self, key=key, value=value), None

    def del_property(self, key):
        """Delete a property.

        :raises Property.DoesNotExist: When the property does not exist.
        """
        if self.property_set.filter(key=key).exists():
            self.property_set.filter(key=key).delete()
        else:
            raise Property.DoesNotExist()

    def __unicode__(self):  # pragma: no cover
        return self.username


class Property(models.Model):
    user = models.ForeignKey(ServiceUser)
    key = models.CharField(max_length=128, db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ('user', 'key')
        permissions = prop_permissions

    def __unicode__(self):  # pragma: no cover
        return "%s: %s=%s" % (self.user.username, self.key, self.value)
