Configuring your webserver
==========================

To make your RestAuth service available to the outside world, you need to configure your webserver.
RestAuth is (more or less) a standard `Django <http://www.djangoproject.com>`_ project, so you can
use any webserver configuration supported by Django. The Django project itself has some
`nice documentation <https://docs.djangoproject.com/en/dev/howto/deployment/>`_ on the subject.

.. Note:: You might want to read this document in the version matching your Django version. 

We provide specialized installation instructions for Apache and mod_wsgi, which is the prefered
solution by both Django and RestAuth. 

Apache and mod_wsgi
-------------------

If you want to run RestAuth as a `mod_wsgi <https://code.google.com/p/modwsgi/>`_ application in
`Apache <https://httpd.apache.org/>`_, a WSGI script is already provided with RestAuth. If you
:doc:`installed from source <../install/from-source>`, the script is included in the :file:`wsgi`
directory. If you installed via our :doc:`APT repositories <../install/debian-ubuntu>` on
Debian/Ubuntu, the file can be found at :file:`/usr/share/doc/restauth/wsgi/restauth`. You can also
fetch it `directly from git <https://git.fsinf.at/restauth/server/blobs/raw/master/wsgi/restauth>`_.

Configuring Apache is very simple, two configuration directives are enough:

.. code-block:: apache

   <VirtualHost *:443>
       ServerName auth.example.com
       # basic configuration...
       #...

       # basic django configuration:
       WSGIScriptAlias / /path/to/your/wsgi-script/restauth
       WSGIPassAuthorization on
   </VirtualHost>

The HTTP Basic authentication is already taken care of by RestAuth itself, you do not have to do
anything to enforce it.

Alternatively, the wsgi script (and thus the webserver) can also perform authentication for the
application. This has the advantage that the webserver takes care of service authentication and it
is potentially harder to exploit any weaknesses in RestAuth. The disadvantage is that HTTP sessions
are unsupported and if enabled, cost considerable performance without being useful in any way.

.. code-block:: apache

   <VirtualHost *:443>
       ServerName auth.example.com
       # basic configuration...
       #...

       # basic django configuration:
       WSGIScriptAlias / /path/to/your/wsgi-script/restauth
       # WSGIPassAuthorization on
       <Location />
           AuthType Basic
           AuthName "RestAuth authentication service"
           AuthBasicProvider wsgi
           Require valid-user

           WSGIAuthUserScript /usr/share/restauth/wsgi/restauth
      </Location>
   </VirtualHost>


For further reading, please also consult `Integration with Django
<http://code.google.com/p/modwsgi/wiki/IntegrationWithDjango>`_ from the mod_wsgi project itself.