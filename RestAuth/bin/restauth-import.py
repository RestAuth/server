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

from datetime import datetime
import os
import sys
import json
import random
import string

# Properties that may also be represented as a UNIX timestamp.
# Otherwise the format must be "%Y-%m-%d %H:%M:%S"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_PROPS = ['date joined', 'last login']

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

try:
    from django.db import transaction

    from RestAuth.Services.models import Service
    from RestAuth.Services.models import ServiceAddress
    from RestAuth.backends.utils import group_backend
    from RestAuth.backends.utils import property_backend
    from RestAuth.backends.utils import user_backend
    from RestAuth.common.cli.parsers import parser
    from RestAuth.common.errors import GroupExists
    from RestAuth.common.errors import PropertyExists
    from RestAuth.common.errors import UserExists
except ImportError, e:
    sys.stderr.write(
        'Error: Cannot import RestAuth. '
        'Please make sure RestAuth is in your PYTHONPATH.\n'
    )
    sys.exit(1)

args = parser.parse_args()

user_backend = user_backend()
property_backend = property_backend()
group_backend = group_backend()

data = json.load(args.file)
if not isinstance(data, dict):
    parser.error("%s: No valid file." % args.file)

services = data.pop('services', {})
users = data.pop('users', {})
groups = data.pop('groups', {})

# test some data structures and fail early if data doesn't look right.
if not isinstance(services, dict):
    parser.error("'services' does not appear to be a dictionary.")
if not isinstance(users, dict):
    parser.error("'users' does not appear to be a dictionary.")
if not isinstance(groups, dict):
    parser.error("'groups' does not appear to be a dictionary.")


def gen_password(length=30):
    punct_chars = [c for c in string.punctuation if c not in ['\'', '\\']]
    punctuation = ''.join(punct_chars)
    chars = string.letters + string.digits + punctuation
    return ''.join(random.choice(chars) for x in range(length))


def init_transaction():
    transaction.enter_transaction_management(args.using)
    transaction.managed(True, args.using)
    user_backend.init_transaction()
    property_backend.init_transaction()
    group_backend.init_transaction()


def commit_transaction():
    transaction.commit()
    user_backend.commit_transaction()
    group_backend.commit_transaction()
    property_backend.commit_transaction()


def rollback_transaction():
    transaction.rollback()
    user_backend.rollback_transaction()
    group_backend.rollback_transaction()
    property_backend.rollback_transaction()


try:
    init_transaction()

    #######################
    ### Import services ###
    #######################
    if services:
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
    if users:
        print('Users:')
    for username, data in users.iteritems():
        username = username.lower()

        try:
            user = user_backend.create(username=username)
            created = True
        except UserExists:
            created = False

        if not created and args.skip_existing_users:
            continue

        # handle password:
        if 'password' in data and (created or args.overwrite_passwords):
            pwd = data['password']
            if type(pwd) == str:
                user_backend.set_password(username=username, password=pwd)
                print('* %s: Set password from input data.' % username)
            elif type(pwd) == dict:
                # TODO: Emit warning if no hasher is found for algorithm
                try:
                    user_backend.set_password_hash(**pwd)
                    print('* %s: Set hash from input data.' % username)
                except NotImplementedError:
                    print("* %s: Setting hash is not supported, skipping." %
                          username)
        elif created and args.gen_passwords:
            raw_passwd = gen_password(30)
            user_backend.set_password(username=username,
                                      password=raw_passwd)
            print('* %s: Generated password: %s' % (username, raw_passwd))
        else:
            print('* %s: User already exists.' % username)

        if 'properties' in data:
            # handle all other preferences
            for key, value in data['properties'].iteritems():
                if key in TIMESTAMP_PROPS:
                    if value.__class__ in [int, float]:
                        value = datetime.fromtimestamp(value)
                    else:  # parse time, to ensure correct format
                        value = datetime.strptime(value, TIMESTAMP_FORMAT)
                    value = datetime.strftime(value, TIMESTAMP_FORMAT)

                if args.overwrite_properties:
                    property_backend.set(user=user, key=key, value=value)
                else:
                    try:
                        property_backend.create(user=user,
                                                key=key, value=value)
                    except PropertyExists:
                        print('%s: Property "%s" already exists.' %
                              (username, key))

    #####################
    ### import groups ###
    #####################
    if groups:
        print("Groups:")
    subgroups = {}
    for name, data in groups.iteritems():
        service = data.pop('service', None)
        if service:
            service = Service.objects.get(username=service)

        try:
            group = group_backend.create(service=service, name=name)
            print("* %s: created." % name)
        except GroupExists:
            if args.skip_existing_groups:
                print("* %s: Already exists, skipping." % name)
                continue
            else:
                print("* %s: Already exists, adding memberships." % name)

        for username in data['users']:
            user = user_backend.get(username=username)
            group_backend.add_user(group=group, user=user)

        if 'subgroups' in data:
            subgroups[group] = data.pop('subgroups')

    # add group-memberships *after* we created all groups to make sure
    # groups already exist.
    for group, subgroups_data in subgroups.iteritems():
        for subgroup_data in subgroups_data:
            name = subgroup_data['name']
            service = subgroup_data.get('service')
            if service:
                service = Service.objects.get(username=service)

            subgroup = group_backend.get(name=name, service=service)
            group_backend.add_subgroup(group=group, subgroup=subgroup)


except Exception as e:
    print("An error occured, rolling back transaction:")
    print("%s: %s" % (type(e), e))
    rollback_transaction()
else:
    commit_transaction()
