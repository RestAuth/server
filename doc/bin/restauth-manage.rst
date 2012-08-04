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

foobar.

Influential environment variables
---------------------------------

.. include:: /includes/env-variables.rst

.. only:: man

   See Also
   ^^^^^^^^

   :manpage:`restauth-service(1)`, :manpage:`restauth-user(1)`,
   :manpage:`restauth-group(1)`, :manpage:`restauth-import(1)`
