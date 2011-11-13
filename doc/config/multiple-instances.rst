Running multiple instances
--------------------------

You might want to run multiple instances of RestAuth on the same host. This would mean that you
effectively have two RestAuth servers (e.g. :samp:`auth.example.com` and :samp:`auth.example.org`),
each with their own users, groups and services. You could maintain two completely separate
installations (maybe even on separate hosts), but that would require twice the maintenance. This
page is dedicated to documenting (known) configuration tips regarding this problem.

General introduction
====================

The only thing that really needs to differ from instance is the database.

If two instances access
the same database, they effectively become the same instance. You could imagine different scenarios,
like one instance requiring a minimum password length of 10 characters and another instance
requiring a minimum password length of 12 characters, but they make little sense. If you desire
such a setup, you can still use any of the following chapters, but examples are based on the
assumption that you want a different database setup.

.. _config_multiple_instances_sni:

Server Name Indication
++++++++++++++++++++++

All examples below use `Server Name Indication (SNI)
<http://en.wikipedia.org/wiki/Server_Name_Indication>`_. That means that the web server (in the
configuration examples, `Apache <http://httpd.apache.org>`_) is able to serve multiple domains on
the same IP via SSL. If you want to use SNI, both client and server need to support it.

On most modern systems, ``server side`` support is not a problem. See the `appropriate chapter
<http://en.wikipedia.org/wiki/Server_Name_Indication#Support>`_ on Wikipedia for more information
on the required software versions. On the client side, the situation is a little more tricky.
`RestAuthClient <https://python.restauth.net>`_ only supports SNI if run with Python 3.2 or later.
`php-restauth <https://php.restauth.net>`_ supports SNI if compiled with OpenSSL/GNU TLS and libcurl
versions that support it.

If using SNI is not an option, the web server can serve different instances on different ports
and/or different IP addresses.

Settings based on environment variables
=======================================

Since :file:`localsettings.py` is just a normal Python file, you can use any Python code you want
in it. The best way of getting multiple instances with the least configuration overhead is by using
environment variables.

First, you must make sure that some environment variable is different for each RestAuth instance you
want to maintain. You can set this anywhere you like, please consult the appropriate documentation
for your web server. The following example sets environment variables in a mod_wsgi deployment.

.. NOTE:: This Apache configuration example uses Server Name Indication. See the :ref:`dedicated
   chapter <config_multiple_instances_sni>` for more information.

.. code-block:: apache

   <VirtualHost *:443>
       ServerName auth.example.com
       # ...
       SetEnv RESTAUTH_HOST auth.example.com
   </VirtualHost>

   <VirtualHost *:443>
       ServerName auth.example.org
       # ...
       SetEnv RESTAUTH_HOST auth.example.org
   </VirtualHost>

You can now use :envvar:`RESTAUTH_HOST` in :file:`localsettings.py` to determine settings based on the
host that the client accesses. To configure different databases, the file might look like this:

.. code-block:: python
   
   # ...
   
   import os
   # get environment variable, .com is the default if undefined
   RESTAUTH_HOST = os.environ.get( 'RESTAUTH_HOST', 'auth.example.com' )
   if RESTAUTH_HOST == 'auth.example.com':
       DATABASES = {
           'default': {
               DATABASE_ENGINE = 'postgresql_psycopg2',
               DATABASE_NAME = 'restauth',
               DATABASE_USER = 'restauth',
               DATABASE_PASSWORD = 'POSTGRES_PASSWORD', # you really should change this!
               DATABASE_HOST = '',
               DATABASE_PORT = '',
           }
       }
   elif RESTAUTH_HOST == 'auth.example.org':
       DATABASES = {
           'default': {
               'ENGINE': 'mysql',
               'NAME': 'restauth',
               'USER': 'restauth',
               'PASSWORD': 'MYSQL_PASSWORD', # you really should change this!
               'HOST': '',
               'PORT': '',
           }
       }
   else:
       raise RuntimeError( 'Unknown RESTAUTH_HOST configured' )
       
In this example, :samp:`auth.example.org` uses a PostgreSQL database and :samp:`auth.example.com`
uses a MySQL database. You can use this setup to set **any other setting** based on the hostname.

Separate settings files
=======================
Another, slightly more maintenance intensive way, is to use different :file:`settings.py` files
altogether. All settings are duplicated in this configuration, if you want to share common
configuration, you can still have them in the file :file:`localsettings.py` as described in the
examples below.

The Apache configuration is similar, only that you use the standard Django environment variable
:envvar:`DJANGO_SETTINGS_MODULE`:

.. NOTE:: This Apache configuration example uses Server Name Indication. See the :ref:`dedicated
   chapter <config_multiple_instances_sni>` for more information.


.. code-block:: apache

   <VirtualHost *:443>
       ServerName auth.example.com
       # ...
       SetEnv DJANGO_SETTINGS_MODULE RestAuth.settings_com
   </VirtualHost>

   <VirtualHost *:443>
       ServerName auth.example.org
       # ...
       SetEnv DJANGO_SETTINGS_MODULE RestAuth.settings_org
   </VirtualHost>
   
You then create two new files, :file:`settings_com.py` and :file:`settings_org.py` in the same
location as :file:`settings.py`. Each file might look like this:

.. code-block:: python

   # First, include settings from settings.py, as it includes useful defaults. If this fails, it
   # generally means that this file is in the wrong location.
   from settings import *

   # now for some settings individual to this installation
   DATABASES = {
       'default': {
           DATABASE_ENGINE = 'postgresql_psycopg2',
           DATABASE_NAME = 'restauth',
           DATABASE_USER = 'restauth',
           DATABASE_PASSWORD = 'POSTGRES_PASSWORD', # you really should change this!
           DATABASE_HOST = '',
           DATABASE_PORT = '',
        }
   }

You can now configure each instance separately. The file :file:`localsettings.py` is still included
in :file:`settings.py`, so you can use it to share settings for every instance.