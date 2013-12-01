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
import traceback

from collections import defaultdict
from datetime import datetime

# Properties that may also be represented as a UNIX timestamp.
# Otherwise the format must be "%Y-%m-%d %H:%M:%S"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_PROPS = ['date joined', 'last login']

# Setup environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RestAuth.settings')
sys.path.append(os.getcwd())

try:
    from django.db import transaction
    from django.utils import six

    from Services.models import Service
    from Services.models import ServiceAddress
    from backends import group_backend
    from backends import property_backend
    from backends import user_backend
    from common.cli.parsers import parser
    from common.errors import GroupExists
    from common.errors import PropertyExists
    from common.errors import UserExists
except ImportError as e:  # pragma: no cover
    sys.stderr.write(
        'Error: Cannot import RestAuth. '
        'Please make sure RestAuth is in your PYTHONPATH.\n'
    )
    sys.exit(1)



def gen_password(length=30):
    punct_chars = [c for c in string.punctuation if c not in ['\'', '\\']]
    punctuation = ''.join(punct_chars)
    chars = string.letters + string.digits + punctuation
    return ''.join(random.choice(chars) for x in range(length))


def init_transaction():
    user_backend.init_transaction()
    property_backend.init_transaction()
    group_backend.init_transaction()


def commit_transaction():
    user_backend.commit_transaction()
    group_backend.commit_transaction()
    property_backend.commit_transaction()


def rollback_transaction():
    user_backend.rollback_transaction()
    group_backend.rollback_transaction()
    property_backend.rollback_transaction()


def save_services(services):
    if services:
        print('Services:')
    for name, data in six.iteritems(services):
        if Service.objects.filter(username=name).exists():
            print('* %s: Already exists.' % name)
            continue

        service = Service(username=name)

        # set password:
        if 'password' in data:
            pwd = data['password']
            if isinstance(pwd, six.string_types):
                service.set_password(pwd)
            elif isinstance(pwd, dict):
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

def save_users(users):
    properties = defaultdict(dict)
    if users:
        print('Users:')
    for username, data in six.iteritems(users):
        username = username.lower()

        try:
            user = user_backend.create(username=username, property_backend=property_backend)
            created = True
        except UserExists:
            user = user_backend.get(username=username)
            created = False

        if not created and args.skip_existing_users:
            continue

        # handle password:
        if 'password' in data and (created or args.overwrite_passwords):
            pwd = data['password']
            if isinstance(pwd, six.string_types):
                user_backend.set_password(username=username, password=pwd)
                print('* %s: Set password from input data.' % username)
            elif isinstance(pwd, dict):
                try:
                    user_backend.set_password_hash(username=username, **pwd)
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

        # handle all other preferences
        for key, value in six.iteritems(data.get('properties', {})):
            if key in TIMESTAMP_PROPS:
                if value.__class__ in [int, float]:
                    value = datetime.fromtimestamp(value)
                else:  # parse time, to ensure correct format
                    value = datetime.strptime(value, TIMESTAMP_FORMAT)
                value = datetime.strftime(value, TIMESTAMP_FORMAT)

            properties[user][key] = value
    return properties

def save_properties(properties):
    for user, props in six.iteritems(properties):
        if args.overwrite_properties:
            property_backend.set_multiple(user, props)
        else:
            for key, value in six.iteritems(props):
                try:
                    property_backend.create(user=user, key=key, value=value)
                except PropertyExists:
                    print('%s: Property "%s" already exists.' %
                          (user.username, key))
                    continue

def save_groups(groups):
    if groups:
        print("Groups:")

    subgroups = {}
    for name, data in six.iteritems(groups):
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
                group = group_backend.get(service=service, name=name)

        for username in data['users']:
            user = user_backend.get(username=username)
            group_backend.add_user(group=group, user=user)

        if 'subgroups' in data:
            subgroups[group] = data.pop('subgroups')

    # add group-memberships *after* we created all groups to make sure
    # groups already exist.
    for group, subgroups_data in six.iteritems(subgroups):
        for subgroup_data in subgroups_data:
            name = subgroup_data['name']
            service = subgroup_data.get('service')
            if service:
                service = Service.objects.get(username=service)

            subgroup = group_backend.get(name=name, service=service)
            group_backend.add_subgroup(group=group, subgroup=subgroup)

def main(args=None):
    args = parser.parse_args(args=args)

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
    try:
        init_transaction()

        with transaction.atomic():
            #######################
            ### Import services ###
            #######################
            save_services(services)

            ####################
            ### import users ###
            ####################
            props = save_users(users)
            save_properties(props)

            #####################
            ### import groups ###
            #####################
            save_groups(groups)

    except Exception as e:
        traceback.print_exc()
        print("An error occured, rolling back transaction:")
        print("%s: %s" % (type(e).__name__, e))
        rollback_transaction()
    else:
        commit_transaction()

if __name__ == '__main__':  # pragma: no cover
    main()
