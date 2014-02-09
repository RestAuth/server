# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

import os
import sys

from pkg_resources import DistributionNotFound
from pkg_resources import Requirement
from pkg_resources import resource_filename

import django.core.handlers.wsgi
_application = django.core.handlers.wsgi.WSGIHandler()

# You may need to add directories to the python path if RestAuth (or one of the
# depending libraries) is not in your path:
#import sys
#sys.path.insert(0, '/some/path/restauth/server')

# Setup environment
try:
    req = Requirement.parse("RestAuth")
    path = resource_filename(req, 'RestAuth')
    if os.path.exists(path):  # pragma: no cover
        sys.path.insert(0, path)
except DistributionNotFound:
    pass  # we're run in a not-installed environment

def application(environ, start_response):
    if 'RESTAUTH_HOST' in environ:
        os.environ['RESTAUTH_HOST'] = environ['RESTAUTH_HOST']
    if 'DJANGO_SETTINGS_MODULE' in environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = environ['DJANGO_SETTINGS_MODULE']
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

    return _application(environ, start_response)

def check_password(environ, user, password):
    try:
        # set up environment:
        from django import db
        db.reset_queries()
        if 'REMOTE_ADDR' in environ:
            host = environ['REMOTE_ADDR']
        else:
            import sys
            sys.stderr.write( "Error: Could not get remote host from environment!" )
            sys.stderr.flush()
            return False

        # verify service
        from Services.models import Service
        try:
            serv = Service.objects.get( username=user )
            if serv.verify( password, host ):
                return True
            else:
                return False
        except Service.DoesNotExist:
            return None
    except Exception, e:
        import sys
        sys.stderr.write( "Error: Uncought exception: %s"%(type(e)) )
        sys.stderr.write( "    %s"%(e) )
        sys.stderr.flush()
        return None
    finally:
        db.connection.close()
