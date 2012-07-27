Creating and configuring a database
-----------------------------------

RestAuth uses a relational database to store its data. You can use any database `supported by Django
<https://docs.djangoproject.com/en/dev/topics/install/?from=olddocs#get-your-database-running>`_.

For RestAuth to use the database, you have to :ref:`create it <database_create>`, :ref:`configure it
<database_configure>` and :ref:`initialize it <config_restauth_initializing_the_database>`.

.. _database_create:

Creating a database
===================

.. NOTE:: Exhaustive documentation on how to create a database is outside the scope of this
   document. If in doubt, always consult the official documentation of your database system.

.. WARNING:: RestAuth requires a database with transactional support. Most notably, the MyISAM MySQL
   storage engine (which is the default on many systems), does **not** support transactions. Please
   use InnoDB instead.

MySQL
"""""

Here is an example shell session for creating a `MySQL <http://www.mysql.com>`_ database:

.. code-block:: bash
   
   mysql -uroot -pYOUR_PASSWORD -e "CREATE DATABASE restauth CHARACTER SET utf8;"
   mysql -uroot -pYOUR_PASSWORD -e "GRANT ALL PRIVILEGES ON restauth.* TO 'restauth'@'localhost'
       IDENTIFIED BY 'MYSQL_PASSWORD';"

The correct ``DATABASES`` setting then would be:

.. code-block:: python
   
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
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
           DATABASE_ENGINE = 'django.db.backends.postgresql_psycopg2',
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

.. _database_configure:

Configuring the database
========================

RestAuth uses the standard `DATABASES setting
<https://docs.djangoproject.com/en/dev/ref/settings/#databases>`_ of Django. Please also see the
`notes for specific database systems <https://docs.djangoproject.com/en/dev/ref/databases/>`_.

To configure your database, just open :file:`localsettings.py` (or :file:`/etc/restauth/settings.py`
if you installed using our Debian/Ubuntu packages) and edit the DATABASES section near
the top of that file.

.. _config_restauth_initializing_the_database:

Initialization
""""""""""""""

Once you have created your database and configured it in :file:`localsettings.py`, you can easily
create the necessary tables using the ``syncdb`` command of :command:`manage.py`. If you installed
from source, you can simply run this inside the :file:`RestAuth/` directory found in the source
code:

.. code-block:: bash
   
   python manage.py syncdb
   
If you used a distribution-specific way to install RestAuth, the command is most likely called
:command:`restauth-manage`:

.. code-block:: bash
   
   restauth-manage syncdb
