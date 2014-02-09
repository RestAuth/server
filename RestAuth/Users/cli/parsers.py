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

from __future__ import unicode_literals

from argparse import ArgumentParser

from common.cli.parsers import pwd_parser
from common.cli.parsers import user_parser
from common.cli.parsers import service_opt_parser


desc = """Manages users in RestAuth. Users are clients that want to
authenticate with services that use RestAuth."""
parser = ArgumentParser(description=desc)

subparsers = parser.add_subparsers(
    title="Available actions", dest='action',
    description="Use '%(prog)s action --help' for more help on each action."
)

# add:
subparser = subparsers.add_parser(
    'add', help="Add a new user.", parents=[user_parser, pwd_parser],
    description="Add a new user."
)
subparser.set_defaults(create_user=True)

# ls:
subparsers.add_parser(
    'ls', help="List all users.", description="List all users.")

# rename
subparser = subparsers.add_parser(
    'rename', help="Rename a user.", parents=[user_parser],
    description='Rename a user.'
)
subparser.add_argument(
    'name', metavar='NAME',
    help="The new name for the user."
)

# verify:
subparsers.add_parser(
    'verify', help="Verify a users password.",
    parents=[user_parser, pwd_parser],
    description="Verify the password of a user."
)

# set-password:
subparsers.add_parser(
    'set-password', parents=[user_parser, pwd_parser],
    help="Set the password of a user.",
    description="Set the password of a user."
)

# rm:
subparsers.add_parser(
    'rm', help="Remove a user.", parents=[user_parser],
    description="Remove a user."
)

user_view_p = subparsers.add_parser(
    'view', parents=[service_opt_parser, user_parser],
    help="View details of a user.", description="View details of a user."
)
