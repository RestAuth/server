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

from RestAuthCommon.error import PreconditionFailed
from RestAuthCommon.error import ResourceConflict
from RestAuthCommon.error import ResourceNotFound


class PasswordInvalid(PreconditionFailed):
    pass


class UsernameInvalid(PreconditionFailed):
    pass


class UserExists(ResourceConflict):
    pass


class PropertyExists(ResourceConflict):
    pass


class GroupExists(ResourceConflict):
    pass


class UserNotFound(ResourceNotFound):
    pass


class PropertyNotFound(ResourceNotFound):
    pass


class GroupNotFound(ResourceNotFound):
    pass
