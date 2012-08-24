#!/usr/bin/env python
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

import os
import sys
import json
import random
import string
import datetime

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

try:
    from RestAuth.common.cli import import_parser

    from RestAuth.Services.models import Service, ServiceAddress
    from RestAuth.Users.models import ServiceUser, Property
    from RestAuth.Groups.models import Group
except ImportError, e:
    sys.stderr.write(
        'Error: Cannot import RestAuth. '
        'Please make sure RestAuth is in your PYTHONPATH.\n'
    )
    sys.exit(1)

args = import_parser.parse_args()

data = json.load(args.file)
services = data.pop('services', None)
users = data.pop('users', None)
groups = data.pop('groups', None)


def gen_password(length=30):
    punct_chars = [c for c in string.punctuation if c not in ['\'', '\\']]
    punctuation = ''.join(punct_chars)
    chars = string.letters + string.digits + punctuation
    return ''.join(random.choice(chars) for x in range(length))


from django.db import transaction
transaction.enter_transaction_management(args.using)
transaction.managed(True, args.using)

try:
    #######################
    ### Import services ###
    #######################
    if services and type(services) != dict:
        print("'services' is not a dictionary, skipping import.")
    elif services:
        print('Services:')
        for name, data in services.iteritems():
            if Service.objects.filter(username=name).exists():
                print('* %s: Already exists.' % name)
                continue

            service = Service(username=name)

            # set password:
            if 'password' in data:
                pwd = data['password']
                if type(pwd) == str:
                    service.set_password(pwd)
                elif type(pwd) == dict:
                    format_tuple = (pwd['algorithm'], pwd['salt'], pwd['hash'])
                    service.password = '%s%s%s' % format_tuple
                print('* %s: Set password from input data.' % name)
            elif args.gen_passwords:
                raw_passwd = gen_password(30)
                service.set_password(raw_passwd)
                print('* %s: Generated password: %s' % (name, raw_passwd))
            service.save()

            if 'hosts' in data:
                for host in data['hosts']:
                    address = ServiceAddress.objects.get_or_create(
                        address=host)[0]
                    service.hosts.add(address)

    ####################
    ### import users ###
    ####################
    if users and type(users) != dict:
        print("'users' not a dictionary, skipping import.")
    elif users:
        print('Users:')

        for username, data in users.iteritems():
            username = username.lower()
            user, created = ServiceUser.objects.get_or_create(
                username=username)

            if not created and args.skip_existing_users:
                continue

            # handle password:
            if 'password' in data and (created or args.overwrite_passwords):
                pwd = data['password']
                if type(pwd) == str:
                    user.set_password(pwd)
                    # if
                elif type(pwd) == dict:
                    user.algorithm = pwd['algorithm']
                    user.salt = pwd.get('salt', None)
                    user.hash = pwd['hash']
                print('* %s: Set password from input data.' % username)
            elif created and args.gen_passwords:
                raw_passwd = gen_password(30)
                user.set_password(raw_passwd)
                print('* %s: Generated password: %s' % (username, raw_passwd))
            else:
                print('* %s: User already exists.' % username)
            user.save()

            if 'properties' in data:
                props = data['properties']
                overwrite_props = args.overwrite_properties

                # handle created, last login
                date_joined_stamp = props.pop('date_joined', None)
                if date_joined_stamp:
                    date_joined = datetime.datetime.fromtimestamp(
                        date_joined_stamp)

                    # set when created:
                    if created:
                        user.date_joined = date_joined
                    # set if we overwrite properties and only if date is
                    # earlier than previous date:
                    elif overwrite_props and user.date_joined > date_joined:
                        user.date_joined = date_joined

                last_login_stamp = props.pop('last_login', None)
                if last_login_stamp:
                    last_login = datetime.datetime.fromtimestamp(
                        elast_login_stamp)

                    # set when created
                    if created:
                        user.last_login = last_login
                    # set if we overwrite properties and only if date is later
                    # than previous date:
                    elif overwrite_properties and user.last_login < last_login:
                        user.last_login = last_login
                user.save()

                # handle all other preferences
                for key, value in props.iteritems():
                    prop, prop_created = Property.objects.get_or_create(
                        user=user, key=key, defaults={'value': value})

                    # overwrite if it already exists and we overwrite
                    # properties:
                    if overwrite_props and not prop_created:
                        prop.value = value
                        prop.save()

    #####################
    ### import groups ###
    #####################
    if groups and type(groups) != dict:
        print("'groups' not a dictionary, skipping import.")
    elif groups:
        print("Groups:")
        subgroups = {}
        for name, data in groups.iteritems():
            service = data.pop('service', None)
            if service:
                service = Service.objects.get(username=service)

            group, created = Group.objects.get_or_create(
                name=name, service=service)
            if created:
                print("* %s: created." % name)
            elif args.skip_existing_groups:
                print("* %s: Already exists, skipping." % name)
                continue
            else:
                print("* %s: Already exists, adding memberships." % name)

            for username in data['users']:
                user = ServiceUser.objects.get(username=username)
                group.users.add(user)

            if 'subgroups' in data:
                subgroups[group] = data.pop('subgroups')

        # add group-memberships *after* we created all groups to make sure
        # groups already exist.
        for group, subgroups_data in subgroups.iteritems():
            for subgroup_data in subgroups_data:
                name, service = subgroup_data['name'], subgroup_data['service']
                if service:
                    service = Service.objects.get(username=service)

                subgroup = Group.objects.get(name=name, service=service)
                group.groups.add(subgroup)


except Exception as e:
    print("An error occured, rolling back transaction:")
    print("%s: %s" % (type(e), e))
    transaction.rollback()
else:
    transaction.commit()
