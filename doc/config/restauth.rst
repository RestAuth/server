Configuring RestAuth
====================

Configuring RestAuth is done like any other Django project in the file :file:`settings.py`. You
should never edit this file, instead always edit the (much better documented)
:file:`localsettings.py`. This file is included by :file:`settings.py` and should, as its name
suggests, set anything that is specific to your local installation. The file includes any settings
you are likely to edit, but you can actually configure any `Django setting
<https://docs.djangoproject.com/en/dev/ref/settings/>`_ you want there.

By default, you have to do very few modifications to :file:`localsettings.py`. The only settings you
*have to* configure are the :ref:`DATABASES <config_restauth_databases>` and :ref:`SECRET_KEY
<config_restauth_secret_key>` settings. 

.. _config_restauth_databases:

DATABASES
---------

This setting is quite flexible, please see the
`Django documentation <https://docs.djangoproject.com/en/dev/ref/settings/#databases>`_ and the
`database specific notes <https://docs.djangoproject.com/en/dev/ref/databases/>`_. You also have
to :ref:`create <config_restauth_creating_a_databases>` and
:ref:`initialize <config_restauth_initializing_the_database>` the database.

.. WARNING:: RestAuth requires a database with transactional support. Most notably, the MyISAM MySQL
   storage engine (which is the default on many systems, does **not** support transactions. Please
   use InnoDB instead.

.. _config_restauth_creating_a_databases:

Creating a database
+++++++++++++++++++

Please note that exhaustive documentation on how to create a database is outside the scope of this
document. If in doubt, always consult the official documentation of your database system.

MySQL
"""""

Here is an example shell session for creating a `MySQL <http://www.mysql.com>`_ database:

.. code-block:: bash
   
   mysql -uroot -pYOUR_PASSWORD -e "CREATE DATABASE restauth CHARACTER SET utf8;"
   mysql -uroot -pYOUR_PASSWORD -e "GRANT ALL PRIVILEGES ON restauth.* TO 'restauth'@'localhost'
       IDENTIFIED BY 'MYSQL_PASSWORD'"

The correct ``DATABASES`` setting then would be:

.. code-block:: python
   
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
   
Please also see the `MySQL notes
<https://docs.djangoproject.com/en/dev/ref/databases/#mysql-notes>`_ (especially the
`Creating your database
<https://docs.djangoproject.com/en/dev/ref/databases/#creating-your-database>`_ chapter) on the
subject. The database tables **must not** use the MyISAM storage engine, please make sure you use
InnoDB or any other engine that supports transactions. Django provides `some instructions
<https://docs.djangoproject.com/en/dev/ref/databases/#creating-your-tables>`_ on how to convert a
database to InnoDB.

PostgreSQL
""""""""""

If you choose to use `PostgreSQL <http://www.postgresql.org>`_, you can create a database like this,
assuming you are already the user ``postgres``:

.. code-block:: bash

   createuser -P restauth
   psql template1 CREATE DATABASE restauth OWNER restauth ENCODING ‘UTF8’;
   
The correct ``DATABASES`` setting then would be:

.. code-block:: python
   
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
   
Please also see the `PostgreSQL notes
<https://docs.djangoproject.com/en/dev/ref/databases/#postgresql-notes>`_ in the Django
documentation.
   
SQLite
""""""

If you are using `SQLite <http://www.sqlite.org/>`_, which is **not recommended** on any production
setup, you do not have to do anything except making sure that the directory named in ``NAME`` is
writable by the webserver.

.. _config_restauth_initializing_the_database:

Initializing the database
+++++++++++++++++++++++++

Once you have created your database, you can easily create the necessary tables using the ``syncdb``
command of :command:`manage.py`. If you installed from source, you can simply run this inside the
:file:`RestAuth/` directory found in the source code:

.. code-block:: bash
   
   python manage.py syncdb
   
If you used a distribution-specific way to install RestAuth, the command is most likely called
:command:`restauth-manage`:

.. code-block:: bash
   
   restauth-manage syncdb
   
.. _config_restauth_secret_key:

SECRET_KEY
----------

Never forget to set a `SECRET_KEY <https://docs.djangoproject.com/en/dev/ref/settings/#secret-key>`_
in :file:`localsettings.py`.

SKIP_VALIDATORS
---------------

By default, usernames in RestAuth can contain any UTF-8 character except a slash ('/'), a backslash
('\\') and a colon (':').

*Validators* are used to restrict usernames further if certain characters are unavailable in some
systems that use your RestAuth installation. Consider the following scenario: Your RestAuth server
provides accounts for a `MediaWiki <http://www.mediawiki.org>`_ (that's also used to register new
accounts) and an `XMPP server
<http://en.wikipedia.org/wiki/Extensible_Messaging_and_Presence_Protocol>`_. MediaWiki has no
problems with usernames containing spaces, but the XMPP protocol forbids that. In this scenario, you
would want the ``xmpp`` validator to block creating users where the username contains a space.

RestAuth ships with validators named ``xmpp``, ``email``, ``mediawiki``, ``linux`` and ``windows``.
You can use the ``SKIP_VALIDATORS`` setting to skip any of the aforementioned validators, by default
``linux``, ``xmpp``, ``email`` and ``windows`` are skipped, because they severely restrict usernames.

.. todo:: Provide an ability to add your own validators.


HASH_ALGORITHM
--------------

The ``HASH_ALGORITHM`` setting configures which algorithm is used for hashing new passwords. If you
set this to a new algorithm, old password hashes will be updated whenever a user logs in. RestAuth
supports all algorithms supported by the `hashlib module
<http://docs.python.org/library/hashlib.html>`_.

In addition, RestAuth supports reading and storing hashes the same way that legacy systems store
them. *Reading* such hashes has the advantage of being able to import user databases from those
systems. *Storing* new hashes this way lets you move the password database back to one of those
systems. Currently the only other supported system is ``mediawiki``. 

LOGGING
-------

Django has very powerful logging configuration capabilities. The full documentation can be found
`in the Django documentation <https://docs.djangoproject.com/en/dev/topics/logging/>`_.

For convenience, RestAuth offers a few additional settings that let you configure the most important
settings and have the rest done by RestAuth. If you are fine with the default, you don't have to do
anything.

* Set the logging using ``LOG_ERROR`` verbosity. See :file:`localsettings.py` for a list of
  available values. The default is ``ERROR``.
* You can define the LoggingHandler (that define where any log messages will go) using
  ``LOG_HANDLER``. The setting should be a string containing the classname of any available handler.
  See `logging.handlers <http://docs.python.org/library/logging.handlers.html>`_ for whats available 
  (of course nothing stops you from implementing your own handler!). The default is
  ``logging.STREAM_HANDLER``.
* You can specify any keyword arguments the LoggingHandler will get using
  ``LOGGING_HANDLER_KWARGS``. You can specify any argument that the LoggingHandler you configured
  supports. The format is a dictionary where the key is string with the name of the keyword arguments
  and the respective value is the value of the keyword argument.
  
Here is a more complex example:

.. code-block:: python

   # we really want to log everything:
   LOG_LEVEL = 'DEBUG'
   # ... and to a socket:
   LOG_HANDLER = 'logging.SOCKET_HANDLER'
   LOG_HANDLER_KWARGS = { 'host': 'localhost', 'port': 10000 }

If you absolutely know what you are doing, you can simply set your own ``LOGGING`` config:

.. code-block:: python
   
   LOGGING = { ... }