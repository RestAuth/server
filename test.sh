#!/bin/bash
#
# This file is part of RestAuth (http://fs.fsinf.at/wiki/RestAuth).
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RestAuth.  If not, see <http://www.gnu.org/licenses/>.

export PYTHONPATH="$PWD"
[ -d ../restauth-common/python ] && export PYTHONPATH="$PYTHONPATH;../restauth-common/python"

rm -f ./RestAuth.sqlite3
python RestAuth/manage.py syncdb --noinput
bin/restauth-service.py --password=vowi add vowi ::1
python RestAuth/manage.py runserver --ipv6
