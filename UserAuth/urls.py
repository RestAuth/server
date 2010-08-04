from django.conf.urls.defaults import *

urlpatterns = patterns( 'RestAuth.UserAuth.views',
        (r'^$', 'create'),
	(r'^(?P<username>\w+)/$', 'user_handler' ),
)
