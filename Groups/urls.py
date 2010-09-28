from django.conf.urls.defaults import *

urlpatterns = patterns( 'RestAuth.Groups.views',
        (r'^$', 'index'),
	(r'^(?P<groupname>[^/]+)/(?P<username>[^/]+)/$', 'member_handler' ),
	(r'^(?P<groupname>[^/]+)/$', 'group_handler' ),
)
