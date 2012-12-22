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

from argparse import Action


class GroupnameAction(Action):
    def __call__(self, parser, namespace, value, option_string):
        # NOTE: we do not get/create database, because --service might be given
        #   afterwards and then we'd get the group with no service.
        groupname = value.lower().decode('utf-8')
        setattr(namespace, self.dest, groupname)
