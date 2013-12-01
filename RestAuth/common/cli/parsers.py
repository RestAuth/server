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

import argparse
import sys

from argparse import ArgumentParser

from common.cli.actions import PasswordGeneratorAction
from common.cli.actions import ServiceAction
from common.cli.actions import UsernameAction
from common.cli.helpers import get_password

service_opt_parser = ArgumentParser(add_help=False)
service_opt_parser.set_defaults(create_service=False)
service_opt_parser.add_argument('--service', action=ServiceAction,
                                help="Act as if %(prog)s was SERVICE.")

user_parser = ArgumentParser(add_help=False)
user_parser.set_defaults(create_user=False)
user_parser.add_argument('user', action=UsernameAction,
                         help="The name of the user.")

pwd_parser = ArgumentParser(add_help=False)
pwd_parser.set_defaults(get_password=get_password, password_generated=False)
pwd_group = pwd_parser.add_mutually_exclusive_group()
pwd_group.add_argument(
    '--password', dest='pwd', metavar='PWD', help="The password to use.")
pwd_group.add_argument(
    '--gen-password', action=PasswordGeneratorAction, nargs=0, dest='pwd',
    help="Generate a password and print it to stdout."
)

##############################
### restauth-import parser ###
##############################
import_desc = "Import user data from another system."
parser = ArgumentParser(description=import_desc)

parser.add_argument(
    '--gen-passwords', action='store_true', default=False,
    help="Generate passwords where missing in input data and print them to "
    "stdout."
)
parser.add_argument(
    '--overwrite-passwords', action='store_true', default=False,
    help='Overwrite passwords of already existing services or users if the'
    'input data contains a password. (default: %(default)s)'
)
parser.add_argument(
    '--overwrite-properties', action='store_true', default=False,
    help='Overwrite already existing properties of users. (default: '
    '%(default)s)'
)
parser.add_argument(
    '--skip-existing-users', action='store_true', default=False,
    help='Skip users completely if they already exist. If not set, passwords '
    'and properties are overwritten if their respective --overwrite-... '
    'argument is given.'
)
parser.add_argument(
    '--skip-existing-groups', action='store_true', default=False,
    help='Skip groups completely if they already exist. If not set, users '
    'and subgroups will be added to the list.'
)
parser.add_argument(
    '--using', default=None, metavar="ALIAS",
    help="Use different database alias. (UNTESTED!)"
)

parser.add_argument(
    'file', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
    help="Input file, defaults to standard input."
)
