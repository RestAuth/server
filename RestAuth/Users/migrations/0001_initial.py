# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=128, db_index=True)),
                ('value', models.TextField()),
            ],
            options={
                'permissions': (('props_list', 'List all properties of a user'), ('prop_create', 'Create a new property'), ('prop_get', 'Get value of a property'), ('prop_set', 'Set or create a property'), ('prop_delete', 'Delete a property')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=60, verbose_name='username')),
                ('password', models.CharField(max_length=256, null=True, verbose_name='password', blank=True)),
            ],
            options={
                'permissions': (('users_list', 'List all users'), ('user_create', 'Create a new user'), ('user_exists', 'Check if a user exists'), ('user_delete', 'Delete a user'), ('user_verify_password', 'Verify a users password'), ('user_change_password', 'Change a users password'), ('user_delete_password', 'Delete a user')),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='property',
            name='user',
            field=models.ForeignKey(to='Users.ServiceUser', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='property',
            unique_together=set([('user', 'key')]),
        ),
    ]
