from django.conf.urls.defaults import *

urlpatterns = patterns( 'RestAuth.Users.views',
        (r'^$', 'create'),
	(r'^(?P<username>[^/]+)/$', 'user_handler' ),
)
