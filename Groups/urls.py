from django.conf.urls.defaults import *

urlpatterns = patterns( 'RestAuth.Groups.views',
        (r'^$', 'index'),
	(r'^(?P<groupname>\w+)/(?P<username>\w+)/$', 'member_handler' ),
	(r'^(?P<groupname>\w+)/$', 'group_handler' ),
)
