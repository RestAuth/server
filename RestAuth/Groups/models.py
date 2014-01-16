# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User as Service
from django.db import models
from django.db.utils import IntegrityError

from Users.models import ServiceUser as User
from Groups.managers import GroupManager

group_permissions = (
    ('groups_for_user', 'List groups for a user'),
    ('groups_list', 'List all groups'),
    ('group_create', 'Create a new group'),
    ('group_exists', 'Verify that a group exists'),
    ('group_delete', 'Delete a group'),
    ('group_users', 'List users in a group'),
    ('group_add_user', 'Add a user to a group'),
    ('group_user_in_group', 'Verify that a user is in a group'),
    ('group_remove_user', 'Remove a user from a group'),
    ('group_groups_list', 'List subgroups of a group'),
    ('group_add_group', 'Add a subgroup to a group'),
    ('group_remove_group', 'Remove a subgroup from a group'),
)


class Group(models.Model):
    service = models.ForeignKey(Service, null=True)
    name = models.CharField(max_length=30, db_index=True)
    users = models.ManyToManyField(User)
    groups = models.ManyToManyField('self', symmetrical=False, related_name='parent_groups')

    objects = GroupManager()

    class Meta:
        unique_together = ('name', 'service')
        permissions = group_permissions

    def get_members(self, depth=None):
        expr = models.Q(group=self)
        if depth is None:
            depth = settings.GROUP_RECURSION_DEPTH

        kwarg = 'group'
        for i in range(depth):
            kwarg += '__groups'
            expr |= models.Q(**{kwarg: self})
        return User.objects.filter(expr).distinct()

    def is_member(self, username):
        return self.get_members().filter(username=username).exists()

    def save(self, *args, **kwargs):
        if self.service is None:
            # some database engines to not enforce unique constraint
            # if service=None
            qs = Group.objects.filter(name=self.name, service=None)
            if self.id:
                qs = qs.exclude(pk=self.id)
            if qs.exists():
                raise IntegrityError("columns name, service_id are not unique")
        super(Group, self).save(*args, **kwargs)

    def __lt__(self, other):  # pragma: py3
        return self.name < other.name

    def __unicode__(self):  # pragma: no cover
        if self.service:
            return "%s/%s" % (self.name, self.service.username)
        else:
            return "%s/None" % (self.name)
