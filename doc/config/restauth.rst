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
subject.

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

If you are using `SQLite <http://www.sqlite.org/>`_, which is not recommended on any production
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
   
If you used any other way of installing RestAuth, the script is most likely called
:command:`restauth-manage`.

.. _config_restauth_secret_key:

SECRET_KEY
----------

SKIP_VALIDATORS
---------------

HASH_ALGORITHM
--------------

LOGGING
-------