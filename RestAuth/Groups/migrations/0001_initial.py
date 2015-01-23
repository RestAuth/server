# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30, db_index=True)),
                ('groups', models.ManyToManyField(related_name='parent_groups', to='Groups.Group')),
                ('service', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('users', models.ManyToManyField(to='Users.ServiceUser')),
            ],
            options={
                'permissions': (('groups_for_user', 'List groups for a user'), ('groups_list', 'List all groups'), ('group_create', 'Create a new group'), ('group_exists', 'Verify that a group exists'), ('group_delete', 'Delete a group'), ('group_users', 'List users in a group'), ('group_add_user', 'Add a user to a group'), ('group_user_in_group', 'Verify that a user is in a group'), ('group_remove_user', 'Remove a user from a group'), ('group_groups_list', 'List subgroups of a group'), ('group_add_group', 'Add a subgroup to a group'), ('group_remove_group', 'Remove a subgroup from a group')),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='group',
            unique_together=set([('name', 'service')]),
        ),
    ]
