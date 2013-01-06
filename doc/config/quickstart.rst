Quickstart to setting up RestAuth
=================================

This is a quickstart guide for getting RestAuth up and running. It assumes a
simple setup with RestAuth as a Apache/WSGI application, a MySQL database and
no complex settings.

Install RestAuth
----------------

Installation instructions are available for a variety of plattforms:

* :doc:`from source </install/from-source>`
* :doc:`Debian/Ubuntu </install/debian-ubuntu>`
* :doc:`Redhat/Fedora </install/redhat-fedora>`
* :doc:`ArchLinux </install/archlinux>`

If your plattform is not listed here, you have to install from source.

Configure RestAuth
------------------

RestAuth has a central configuration file called |file-settings-link|. The
location varies depending on how you installed RestAuth. Follow the previous
link to get an overview where this file might me stored.

The configuration file is a plain Python file. Don't worry if you have no
experience writing Python, the syntax is pretty straight forward. Be careful of
syntax errors, though, as this would cause hard-to-debug errors.

The only settings you really have to make are the ``DATABASES`` and the
``SECRET_KEY`` settings, which are almost at the beginning of the file. After
your editing, the relevant sections should look like this:

.. code-block:: python
    :linenos:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'restauth', # Or path to database file if using sqlite3.
            'USER': 'restauth',                      # Not used with sqlite3.
            'PASSWORD': 'changeme',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.

            # REMOVE THIS AFTER YOU CREATED YOUR DATABASE:
            'OPTIONS': {
                'init_command': 'SET storage_engine=INNODB',
            },
        }
    }

    # ...
    SECRET_KEY='pleasechangethisstring'

.. WARNING:: Please do not forget to set the password for the database (line 6)
   and SECRET KEY (line 18) to some random string. The two strings should not be
   the same strings.

Feel free to look around the config-file, it has lots of comments to make it
easy for you to customize RestAuth to your needs.

Create a database
-----------------

The next step is creating your database (:ref:`detailed instructions
<database_create>`). This is done by two simple commands on the shell:

.. code-block:: bash

   mysql -uroot -pYOUR_PASSWORD -e "CREATE DATABASE restauth CHARACTER SET utf8;"
   mysql -uroot -pYOUR_PASSWORD -e "GRANT ALL PRIVILEGES ON restauth.* TO 'restauth'@'localhost' IDENTIFIED BY 'changeme';"

.. WARNING:: Please set the password ('changeme') to whatever you configured in
   your config-file.

On some systems (i.e. Debian based systems) there is no root-password for MySQL
and you connect, as root system user, using a config-file. Here is an example
for Debian/Ubuntu:

.. code-block:: bash

   mysql --defaults-file=/etc/mysql/debian.cnf -e "CREATE DATABASE matitest CHARACTER SET utf8;"
   mysql --defaults-file=/etc/mysql/debian.cnf -e "GRANT ALL PRIVILEGES ON restauth.* TO 'restauth'@'localhost' IDENTIFIED BY 'changeme';"

Setup database
--------------

Next you need to populate your database with the necessary tables. This
couldn't be simpler, using |bin-restauth-manage-link|:

.. parsed-literal::

   |bin-restauth-manage| syncdb --noinput
   |bin-restauth-manage| migrate

Configure Webserver
-------------------

Note that :doc:`more detailed documentation </config/webserver>` is available.

.. only:: not debian

   Add daemon user
   _______________

.. only:: homepage

   .. NOTE:: This step is not necessary if you installed using our Debian/Ubuntu
      packages, as the user is added automatically.

.. only:: not debian

   In this setup, RestAuth WSGI daemons run as a dedicated system user. Depending
   on the system, you first need to create this user:

   .. code-block:: bash

      adduser --system --group --home /path/to/sources --no-create-home --disabled-login restauth

   The home-directory is basically irrelevant but it should exist.

Add Apache virtual host
_______________________

.. NOTE:: General Apache webserver setup is outside the scope of this document.
   Please consult the (excellent) Apache documentation for more information.

Next you need to actually configure your Webserver. It is recommended to add a
dedicated virtual host. The exact locations of Apache webserver configuration
files and what your basic (virtual) host setup is greatly depends on your
plattform. Here are the relevant parts for RestAuth:

.. code-block:: apache
    :linenos:

    <VirtualHost *:443>
        # your basic configuration here...

        # Django/WSGI application
        WSGIScriptAlias / /path/to/your/wsgi-script/restauth
        WSGIPassAuthorization on
        WSGIProcessGroup restauth
        WSGIDaemonProcess restauth user=restauth group=restauth processes=1 threads=10
    </VirtualHost>

.. vim syntax highlighting for rst sucks*

The wsgi-script (see line 5) is located in different locations depending on how you installed
RestAuth:

* from source: ``wsgi/restauth`` of your source folder
* on Debian/Ubuntu: ``/usr/share/restauth/wsgi/restauth``
* on Redhat/Fedora: unkown.
* on ArchLinux: ``/usr/share/restauth/wsgi/restauth``

Don't forget to restart your Apache after you've added the configuration.

Add services that use RestAuth
------------------------------

The final step to get a working RestAuth server is to add services to RestAuth.
A service is a system (i.e. a Wiki, a CMS, a Unix system, ...) that uses
RestAuth. RestAuth needs to know about the services using it, where they connect
from and what they are allowed to do. Managing services is done via
|bin-restauth-service-doc|. Adding a service works like this:

.. parsed-literal::

   |bin-restauth-service| add --gen-password wiki.example.com
   |bin-restauth-service| set-hosts 127.0.0.1
   |bin-restauth-service| set-permissions users_list user_verify_password user_change_password

In the above example the command in line 1 adds the service. A generated
password is printed to standard output. Use these credentials in the
configuration of the service that uses RestAuth. The command in line 2 specifies
that the service connects from 127.0.0.1 (that is, it runs on the same machine
as the RestAuth server). Line 3 specifies that the service is allowed to get a
list of all users, verify and change user passwords.

Further reading
---------------

The most recommended pages in this documentation are:

* A complete reference of :doc:`all configuration variables
  </config/all-config-values>`
* Documentation for the cli tools:

  * |bin-restauth-manage-doc|
  * |bin-restauth-service-doc|
  * |bin-restauth-user-doc|
  * |bin-restauth-group-doc|
  * |bin-restauth-import-doc|

* Solutions for :doc:`importing existing user databases into RestAuth
  </migrate/overview>`
