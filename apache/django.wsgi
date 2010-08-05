import os
import sys
sys.path.append('/home/mati/RestAuth/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

