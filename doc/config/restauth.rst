Configuring RestAuth
====================

RestAuth is configured like any other Django project, in the file :file:`settings.py`. You
should never edit this file directly, instead always edit the (much better documented)
:file:`localsettings.py`. This file is included by :file:`settings.py` and should, as its name
suggests, set anything that is specific to your local installation. The file includes any settings
you are likely to edit, but you can actually configure any `Django setting
<https://docs.djangoproject.com/en/dev/ref/settings/>`_ you want there. Please consult
:doc:`Settings </config/all-config-values>` on noteworthy configuration variables.


By default, you have to do very few modifications to :file:`localsettings.py`. The only settings you
*have to* configure are the :ref:`DATABASES <config_restauth_databases>` and :setting:`SECRET_KEY`
settings. 

.. _config_restauth_databases:

Creating a database
-------------------

The `DATABASES <https://docs.djangoproject.com/en/dev/ref/settings/#databases>`_ setting is quite
flexible. Please also consult the `database specific notes
<https://docs.djangoproject.com/en/dev/ref/databases/>`_ for any particularities of your Database
system. You have to create and :ref:`initialize <config_restauth_initializing_the_database>`
the database.

.. NOTE:: Exhaustive documentation on how to create a database is outside the scope of this
   document. If in doubt, always consult the official documentation of your database system.

.. WARNING:: RestAuth requires a database with transactional support. Most notably, the MyISAM MySQL
   storage engine (which is the default on many systems, does **not** support transactions. Please
   use InnoDB instead.

Create a MySQL database
"""""""""""""""""""""""

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

Create a PostgreSQL database
""""""""""""""""""""""""""""

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