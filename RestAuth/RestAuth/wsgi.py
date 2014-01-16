import os

import django.core.handlers.wsgi
_application = django.core.handlers.wsgi.WSGIHandler()

# You may need to add directories to the python path if RestAuth (or one of the
# depending libraries) is not in your path:
#import sys
#sys.path.insert(0, '/some/path/restauth/server')

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
