from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^RestAuth/', include('RestAuth.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^/?$', 'RestAuth.views.index' ),
    (r'^admin/',  include('admin.site.urls')),
    (r'^users/',  include('RestAuth.Users.urls')),
    (r'^userprops/',  include('RestAuth.Users.prop-urls')),
    (r'^groups/', include('RestAuth.Groups.urls')),
)
