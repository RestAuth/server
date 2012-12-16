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

from argparse import ArgumentParser

from RestAuth.common.cli import pwd_parser, service_arg_parser


desc = """%(prog)s manages services in RestAuth. Services are websites,
hosts, etc. that use RestAuth as authentication service."""
service_parser = ArgumentParser(description=desc)

subparsers = service_parser.add_subparsers(
    title='Available actions', dest='action',
    description='Use "%(prog)s action --help" for more help on each action.')
subparsers.add_parser(
    'add', help="Add a new service.", description="Add a new service.",
    parents=[pwd_parser, service_arg_parser]
)
subparsers.add_parser(
    'ls', help="List all services.",
    description="""List all available services."""
)
subparsers.add_parser(
    'rm', help="Remove a service.", parents=[service_arg_parser],
    description='Completely remove a service. This will also remove any '
    'groups associated with that service.'
)
subparsers.add_parser(
    'view', help="View details of a service.", parents=[service_arg_parser],
    description="View details of a service."
)

subparser = subparsers.add_parser(
    'set-hosts', parents=[service_arg_parser],
    help='Set hosts that a service can connect from, removes any previous '
    'hosts.',
    description='Set hosts that a service can connect from.'
)
subparser.add_argument(
    'hosts', metavar='HOST', nargs='*',
    help='Hosts that this service is able to connect from. Note: This must be '
    'an IPv4 or IPv6 address, NOT a hostname.'
)
subparser = subparsers.add_parser(
    'add-hosts', parents=[service_arg_parser],
    help="Add hosts that a service can connect from.",
    description="Add hosts that a service can connect from."
)
subparser.add_argument(
    'hosts', metavar='HOST', nargs='+',
    help='Add hosts that this service is able to connect from. Note: This '
    'must be an IPv4 or IPv6 address, NOT a hostname.'
)
subparser = subparsers.add_parser(
    'rm-hosts', parents=[service_arg_parser],
    help='Remove hosts that a service can connect from.',
    description='Remove hosts that a service can connect from.'
)
subparser.add_argument(
    'hosts', metavar='HOST', nargs='+',
    help='Remove hosts that this service is able to connect from. Note: This '
    'must be an IPv4 or IPv6 address, NOT a hostname.'
)

subparsers.add_parser(
    'set-password', parents=[service_arg_parser, pwd_parser],
    help="Set the password for a service.",
    description="Set the password for a service."
)
subparser = subparsers.add_parser(
    'add-permissions', parents=[service_arg_parser],
    help="Add permissions to a service.",
    description='Add permissions to a service. This command supports shell '
    "wildcard style expansions, so 'user*' will add all user permissions.",
    epilog='Please see the man-page for available permissions.'
)
subparser.add_argument(
    'permissions', metavar='PERM', nargs='+',
    help="Permissions to add to the specified service."
)
subparser = subparsers.add_parser(
    'rm-permissions', parents=[service_arg_parser],
    help="Remove permissions from a service.",
    description='Remove permissions from a service. This command supports '
    'shellwildcard style expansions, so "user*" will remove all user '
    'permissions.',
    epilog='Please see the man-page for available permissions.'
)
subparser.add_argument(
    'permissions', metavar='PERM', nargs='+',
    help='Permissions to remove from the specified service. Possible '
    'permissions are: %s'
)
subparser = subparsers.add_parser(
    'set-permissions', parents=[service_arg_parser],
    help='Set permissions of a service, removes any previous permissions.',
    description='Set permissions of a service, removes any previous '
    'permissions. This command supports shell wildcard style expansions, so '
    '"user*" will set all user permissions.',
    epilog='Please see the man-page for available permissions.'
)
subparser.add_argument(
    'permissions', metavar='PERM', nargs='*',
    help="Set the permissions of the specified service. Possible permissions "
    "are: %s"
)
