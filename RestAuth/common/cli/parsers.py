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

from RestAuth.common.cli.actions import UsernameAction, PasswordGeneratorAction

user_parser = ArgumentParser(add_help=False)
user_parser.set_defaults(create_user=False)
user_parser.add_argument('user', action=UsernameAction,
                         help="The name of the user.")

pwd_parser = ArgumentParser(add_help=False)
pwd_group = pwd_parser.add_mutually_exclusive_group()
pwd_group.add_argument(
    '--password', dest='pwd', metavar='PWD', help="The password to use.")
pwd_group.add_argument(
    '--gen-password', action=PasswordGeneratorAction, nargs=0, dest='pwd',
    help="Generate a password and print it to stdout."
)
