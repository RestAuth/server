import os, sys
sys.path.append('/usr/local/share/RestAuth/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
