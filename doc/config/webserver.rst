Configuring your webserver
==========================

To make your RestAuth service available to the outside world, you need to
configure your webserver.  RestAuth is (more or less) a standard `Django`_
project, so you can use any webserver configuration supported by Django. The
Django project itself has some `nice documentation
<https://docs.djangoproject.com/en/dev/howto/deployment/>`_ on the subject.

.. Note:: You might want to read this document in the version matching your Django version.

We provide specialized installation instructions for Apache and mod_wsgi, which is the prefered
solution by both Django and RestAuth.

Apache and mod_wsgi
-------------------

If you want to run RestAuth as a `mod_wsgi <https://code.google.com/p/modwsgi/>`_ application in
`Apache <https://httpd.apache.org/>`_, a WSGI script is already provided with RestAuth. If you
:doc:`installed from source <../install/from-source>`, the script is included in the :file:`wsgi`
directory. If you installed via our :doc:`APT repositories <../install/debian-ubuntu>` on
Debian/Ubuntu, the file can be found at :file:`/usr/share/restauth/wsgi/restauth`. You can also
fetch it `directly from git <https://git.fsinf.at/restauth/server/blobs/raw/master/wsgi/restauth>`_.

Configuring Apache is very simple, only the basic WSGI configuration directives are needed:

.. code-block:: apache

   <VirtualHost *:443>
       ServerName auth.example.com
       # basic configuration...
       #...

       # basic django configuration:
       WSGIScriptAlias / /path/to/your/wsgi-script/restauth
       WSGIPassAuthorization on

       # if you want to run WSGI processes as their own user:
       WSGIProcessGroup restauth
       WSGIDaemonProcess restauth user=restauth group=restauth processes=1 threads=10
   </VirtualHost>

.. vim syntax-higlighiting suxx*

The HTTP Basic Authentication is already taken care of by RestAuth itself as long as you set
``WSGIPassAuthorization on`` in the Apache configuration.

.. NOTE:: It is recommended to run the RestAuth WSGI application as its own user. The Debian
   packages already add a user called ``restauth``. If you install from source, you can create a
   user using:

   .. code-block:: bash

      user@host:~ $ adduser --system --group --home /path/to/sources --no-create-home --disabled-login restauth

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

       # if you want to run WSGI processes as their own user:
       WSGIProcessGroup restauth
       WSGIDaemonProcess restauth user=restauth group=restauth processes=1 threads=10

       <Location />
           AuthType Basic
           AuthName "RestAuth authentication service"
           AuthBasicProvider wsgi
           Require valid-user

           WSGIAuthUserScript /path/to/your/wsgi-script/restauth
      </Location>
   </VirtualHost>

.. vim syntax-highlighting sux.*

For further reading, please also consult `Integration with Django
<http://code.google.com/p/modwsgi/wiki/IntegrationWithDjango>`_ from the mod_wsgi project itself.

uWSGI
-----

You can also run RestAuth using `uWSGI <http://projects.unbit.it/uwsgi/>`_. You
will still need to run a webserver, but it only needs very little configuration.
This setup works especially well if you want to run RestAuth inside a
*virtualenv*, because uWSGI is available via pip. Here is a full walkthrough for
setting up RestAuth with MySQL and memcached, from the start::

   # Install dependencies, adapt to your system if you don't use Debian/Ubuntu.
   # Note that all other dependencies are only installed inside the virtual
   # environment.
   root@host:~$ apt-get install git python-virtualenv python-pip memcached mysql-server libapache2-mod-uwsgi

   # Create the database:
   root@host:~$ mysql --defaults-file=/etc/mysql/debian.cnf -e "CREATE DATABASE restauth CHARACTER SET utf8;"
   root@host:~$ mysql --defaults-file=/etc/mysql/debian.cnf -e "GRANT ALL PRIVILEGES ON restauth.* TO 'restauth'@'localhost' IDENTIFIED BY 'MYSQL_PASSWORD';"

   # Add a daemon user:
   root@host:~$ adduser --system --group --home /usr/local/home/restauth --disabled-login restauth
   root@host:~$ sudo su restauth -s /bin/bash
   restauth@host:/root$ cd

   # Create some runtime directories:
   restauth@host:~$ mkdir run log

   # Clone source:
   restauth@host:~$ git clone https://git.fsinf.at/restauth/server.git
   restauth@host:~$ cd server/

   # Create virtualenv, install dependencies:
   restauth@host:server$ virtualenv .
   restauth@host:server$ source bin/activate
   (server)restauth@host:server$ pip install -r requirements.txt
   (server)restauth@host:server$ pip install -U distribute # mysql needs distribute >= 0.6.28
   (server)restauth@host:server$ pip install uWSGI MySQL-python python-memcached

   # Edit RestAuth/localsettings.py.
   # The file is well-documented and contains many links to further
   # documentation. Especially configure the DATABASES, VALIDATORS and CACHES
   # settings.
   (server)restauth@host:server$ vim RestAuth/localsettings.py

   # Setup the database:
   (server)restauth@host:server$ python RestAuth/manage.py syncdb --noinput
   (server)restauth@host:server$ python RestAuth/manage.py migrate

   # Set up a service that might access the RestAuth service:
   (server)restauth@host:server$ bin/restauth-service.py add wiki.example.com
   (server)restauth@host:server$ bin/restauth-service.py set-hosts wiki.example.com 127.0.0.1 ::1
   (server)restauth@host:server$ bin/restauth-service.py set-permissions wiki.example.com user* group* prop*

   # Add uwsgi configuration file - see below.
   (server)restauth@host:server$ vim uwsgi.ini

   # Configure webserver to proxy requests to uWSGI - see below.

   # Thats it - we only need to start uwsgi now:
   (server)restauth@host:server$ uwsgi --ini uwsgi.ini

You can start/reload/etc. the instances with::

   (server)restauth@host:server$ uwsgi --ini uwsgi.ini --stop
   (server)restauth@host:server$ uwsgi --ini uwsgi.ini --reload

The uWSGI configuration file should look like this::

   [uwsgi]
   chdir=/usr/local/home/restauth/server
   wsgi-file=/usr/local/home/restauth/server/wsgi/restauth
   virtualenv=/usr/local/home/restauth/server
   socket=127.0.0.1:3031
   master=True
   pidfile=/usr/local/home/restauth/run/master.pid
   vacuum=True
   max-requests=5000
   env=DJANGO_SETTINGS_MODULE=RestAuth.settings
   daemonize=/usr/local/home/restauth/log/uwsgi.log

Configure webserver
___________________

The uWSGI documentation has `many examples
<http://projects.unbit.it/uwsgi/wiki/Example>`_. This is how an apache config
would look like for the uwsgi.ini given above.

.. code-block:: apache

   <Location />
       SetHandler uwsgi-handler
       uWSGISocket 127.0.0.1:3031
   </Location>
