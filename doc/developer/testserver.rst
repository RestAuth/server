Run a testserver
----------------

When you want to develop a client library and want to build testcases that use a
running RestAuth instance, you can easily run a testserver on your own.

.. NOTE:: The testserver uses an in-memory SQLite database and never touches any
   existing databases, it should even be save to run this on production systems.

Use virtualenv
==============

The quickest way to get a testserver running is using virtualenv, which creates
isolated Python environments. Using virtualenv, your system is not polluted
with dependencies. Setting up a virtualenv is very simple:

.. code-block:: bash

   virtualenv .
   source bin/activate
   pip install -r requirements.txt

.. NOTE:: If you don't have :command:`pip` installed, you have to install it
   using :command:`easy_install pip`.

Run default testserver
======================

You can run a testserver simply by executing

.. code-block:: bash

   python setup.py testserver

This will create a testserver listing on ``::1``, port 8000. The testserver has
some services preconfigured:

=================== ======== =================================================
service             password Notes
=================== ======== =================================================
vowi                nopass   Used by most unittests in client libraries.
                             Has all permissions. Primarily there for
                             historical reasons, use example.* services
                             instead.
example.com         nopass   Has all permissions.
example.org         nopass   Has all permissions and the group ``orggroup``
                             predefined.
example.net         nopass   Only has group-permissions and the predefined
                             group ``netgroup``, which is a subgroup of the
                             group ``orggroup`` in the ``example.org`` service.
nohosts.example.org nopass   Does have all permissions, but you can't connect
                             to it from anywhere, because no hosts are defined
                             for it.
=================== ======== =================================================

No users or properties are preconfigured.

Running a custom testserver
===========================

It might be necessary for you to run a custom testserver. To do so, you have to
use |bin-restauth-manage-doc| directly to start the testserver. The equivalent
to the above ``setup.py`` is:

.. code-block:: bash

   python RestAuth/manage.py testserver --ipv6 RestAuth/fixtures/testserver.json

The ``testserver`` command provides a variety of options, simply run:

.. code-block:: bash

   python RestAuth/manage.py testserver --help

for a comprehensive list.

You might need your own testdata (for example, with some users and/or groups
preconfigured), in which case you have to create a `fixture
<https://docs.djangoproject.com/en/dev/howto/initial-data/>`_. To do this,
create a fresh database, add all necessary data and dump the data to a new
fixture:

.. code-block:: bash

   # create empty database:
   python RestAuth/manage.py syncdb --noinput
   python RestAuth/manage.py migrate
   python RestAuth/manage.py flush --noinput

   # create testdata:
   RestAuth/bin/restauth-service.py add --password=foobar example.com
   RestAuth/bin/restauth-service.py set-hosts example.com ::1
   RestAuth/bin/restauth-service.py set-permissions example.com user* group* prop*
   RestAuth/bin/restauth-user.py add --password=example example

   # create fixture:
   python RestAuth/manage.py dumpdata > /path/to/your/library/fixtures/testserver.json

You can then run the testserver with your new fixture by running:

.. code-block:: bash

   python RestAuth/manage.py testserver --ipv6 /path/to/your/library/fixtures/testserver.json
