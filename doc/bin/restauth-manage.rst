restauth-manage
===============

.. only:: html

   |bin-restauth-manage-as-cmd| is the Django manage.py script that usually ships with
   Django projects. Please see `the official Django documentation
   <https://docs.djangoproject.com/en/dev/ref/django-admin/>`_
   for more information.

.. only:: man

   Synopsis
   --------

   |bin-restauth-manage-bold| [**-h**] *command* [*option*] ... [*args*] ...

   Description
   -----------

   |bin-restauth-manage| is the Django manage.py script that usually ships with
   Django projects. Please see::

      https://docs.djangoproject.com/en/dev/ref/django-admin/

   for more information.
.. only:: homepage

   .. _dist-specific-bin-restauth-manage:

   Location of |bin-restauth-manage-as-cmd|
   ----------------------------------------

   If you :doc:`installed from source </install/from-source>`, this script is
   not automatically put in your path. Instead, the script is included as
   :file:`manage.py` to the location setuptools installed to. On Unix
   or Linux systems, this usually is
   :file:`/usr/local/lib/python2.{x}/dist-packages/RestAuth`. You can find the
   exact installation location using the following shell command:

   .. code-block:: bash

      python -c "import RestAuth; print RestAuth.__file__"

   If you Installed via your distributions packaging tools, the script should
   be in your PATH and you can start it by just typing
   |bin-restauth-manage-as-cmd|.

Interesting |bin-restauth-manage-as-cmd| commands
-------------------------------------------------

Several commands for |bin-restauth-manage| are worth noting:

.. todo:: document interesting command

.. only:: not man

   syncdb
   ^^^^^^

.. example:: **syncdb** [**--noinput**]

   The standard `syncdb
   <https://docs.djangoproject.com/en/dev/ref/django-admin/#django-admin-syncdb>`_
   command. This command creates all database tables that don't yet exist in the
   database you configured in |file-settings-link|.

   .. NOTE:: If you execute ``syncdb`` without the ``--noinput`` parameter, you
      will be asked if you want to create a *user*. This user is equivalent to
      service added with |bin-restauth-service-link|, not a user added with
      |bin-restauth-user-link|.

.. only:: not man

   migrate
   ^^^^^^^

.. example:: **migrate**

   Used to bring the database schema to the newest state.

.. only:: not man

   dbshell
   ^^^^^^^

.. example:: **dbshell**

   Open a database shell to the database you configured in
   |file-settings-link|. Also see the `official documentation
   <https://docs.djangoproject.com/en/dev/ref/django-admin/#dbshell>`_.

.. only:: not man

   shell
   ^^^^^

.. example:: **shell**

   Open a python shell (using ipython if available) with your settings
   preconfigured. Also see the `official documentation
   <https://docs.djangoproject.com/en/dev/ref/django-admin/#shell>`_.



Influential environment variables
---------------------------------

.. include:: /includes/env-variables.rst

.. only:: man

   See Also
   ^^^^^^^^

   :manpage:`restauth-service(1)`, :manpage:`restauth-user(1)`,
   :manpage:`restauth-group(1)`, :manpage:`restauth-import(1)`
