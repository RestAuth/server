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

import os, sys, getpass, fnmatch

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'
sys.path.append(os.getcwd())

try:
    from RestAuth.Services.models import *
    from RestAuth.common.cli import pwd_parser, service_parser
    
    from RestAuth.Users.models import user_permissions, prop_permissions
    from RestAuth.Groups.models import group_permissions
except ImportError, e:
    print(e)
    sys.stderr.write('Error: Cannot import RestAuth. Please make sure RestAuth is in your PYTHONPATH.\n')
    sys.exit(1)

args = service_parser.parse_args()

def get_password(args):
    if args.pwd:
        return args.pwd

    password = getpass.getpass('password: ')
    confirm = getpass.getpass('confirm: ')
    if password != confirm:
        print("Passwords do not match, please try again.")
        return get_password(args)
    else:
        return password

def parse_permissions(raw_permissions):
    user_ct = ContentType.objects.get(app_label='Users', model='serviceuser')
    prop_ct = ContentType.objects.get(app_label='Users', model='property')
    group_ct = ContentType.objects.get(app_label='Groups', model='group')
    
    user_permissions_dict = dict(user_permissions)
    prop_permissions_dict = dict(prop_permissions)
    group_permissions_dict = dict(group_permissions)
    
    permissions = []
    for raw_permission in raw_permissions:
        for codename in fnmatch.filter(user_permissions_dict.keys(), raw_permission):
            perm, c = Permission.objects.get_or_create(
                content_type=user_ct, codename=codename,
                defaults={'name': user_permissions_dict[codename]}
            )
            permissions.append(perm)
            
        for codename in fnmatch.filter(prop_permissions_dict.keys(), raw_permission):
            perm, c = Permission.objects.get_or_create(
                content_type=prop_ct, codename=codename,
                defaults={'name': prop_permissions_dict[codename]}
            )
            permissions.append(perm)
        
        for codename in fnmatch.filter(group_permissions_dict.keys(), raw_permission):
            perm, c = Permission.objects.get_or_create(
                content_type=group_ct, codename=codename,
                defaults={'name': group_permissions_dict[codename]}
            )
            permissions.append(perm)
        
    return permissions

if args.action in ['create', 'add']:
    try:
        check_service_username(args.service)
        service = Service(username=args.service)
        service.save()
        service.set_password(get_password(args))
        service.save()
    except IntegrityError as e:
        print("Error: %s: Service already exists."%args.service)
        sys.exit(1)
    except ServiceUsernameNotValid as e:
        print(e)
        sys.exit(1)
elif args.action in [ 'remove', 'rm', 'del', 'delete' ]:
    try:
        service = Service.objects.get(username=args.service)
        service.delete()
    except Service.DoesNotExist:
        print("Error: %s: Service not found."%args.service)
        sys.exit(1)
elif args.action in [ 'list', 'ls' ]:
    for service in Service.objects.all():
        hosts = [ str(host.address) for host in service.hosts.all() ]
        print('%s: %s'%(service.username, ', '.join(hosts)))
elif args.action == 'view':
    try:
        service = Service.objects.get(username=args.service)
        print(service.username)
        print('Last used: %s' % (service.last_login))
        hosts = [ str(host.address) for host in service.hosts.all()]
        print('Hosts: %s' % (', '.join(hosts)))
        perms = [p.codename for p in service.user_permissions.all()]
        print('Permissions: %s' % (', '.join(perms)))
    except Service.DoesNotExist:
        print("Error: %s: Service not found."%args.service)
        sys.exit(1) 
elif args.action == 'set-hosts':
    try:
        service = Service.objects.get(username=args.service)
        service.set_hosts(*args.hosts)
    except Service.DoesNotExist:
        print("Error: %s: Service not found."%args.service)
        sys.exit(1)
elif args.action == 'add-hosts':
    try:
        service = Service.objects.get(username=args.service)
        service.add_hosts(*args.hosts)
    except Service.DoesNotExist:
        print("Error: %s: Service not found."%args.service)
        sys.exit(1)
elif args.action == 'rm-hosts':
    try:
        service = Service.objects.get(username=args.service)
        service.del_hosts(*args.hosts)
    except Service.DoesNotExist:
        print("Error: %s: Service not found."%args.service)
        sys.exit(1)
elif args.action == 'set-password':
    try:
        service = Service.objects.get(username=args.service)
        service.set_password(get_password(args))
        service.save()
    except Service.DoesNotExist:
        print("Error: %s: Service not found."%args.service)
        sys.exit(1)
elif args.action == 'set-permissions':
    try:
        service = Service.objects.get(username=args.service)
        perms = parse_permissions(args.permissions)
        service.set_permissions(perms)
    except Service.DoesNotExist:
        print("Error: %s: Service not found." % args.service)
        sys.exit(1)
elif args.action == 'add-permissions':
    try:
        service = Service.objects.get(username=args.service)
        perms = parse_permissions(args.permissions)
        service.add_permissions(perms)
    except Service.DoesNotExist:
        print("Error: %s: Service not found." % args.service)
        sys.exit(1)
elif args.action == 'rm-permissions':
    try:
        service = Service.objects.get(username=args.service)
        perms = parse_permissions(args.permissions)
        service.rm_permissions(perms)
    except Service.DoesNotExist:
        print("Error: %s: Service not found." % args.service)
        sys.exit(1)
