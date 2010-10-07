from django.conf.urls.defaults import *

urlpatterns = patterns( 'RestAuth.Users.views',
	(r'^(?P<username>[^/]+)/$', 'userprops_index' ),
	(r'^(?P<username>[^/]+)/(?P<prop>.+)/$', 'userprops_prop' ),
)
