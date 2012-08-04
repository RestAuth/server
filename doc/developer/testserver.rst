Run a testserver
----------------

When you want to develop a client library and want to build testcases that use a running RestAuth
instance, you can easily run a testserver on your own.

.. NOTE:: The testserver uses an in-memory SQLite database and never touches any existing databases,
   it should even be save to run this on production systems.

Run default testserver
======================

You can run a testserver simply by executing

.. code-block:: bash

   python setup.py testserver

This will create a testserver listing on ``::1``, port 8000. The testserver has some services
preconfigured:

======= ======== ==============
service password services
======= ======== ==============
vowi    vowi     ::1
fsinf   fsinf    ::1
test1   test1
test2   test2    ::1, 127.0.0.1
test3   test3    ::3
======= ======== ==============

No users, properties or groups are preconfigured.

Running a custom testserver
===========================

It might be necessary for you to run a custom testserver. To do so, you have to use
|bin-restauth-manage-doc| directly to start the testserver. The equivalent to the
above ``setup.py`` is:

.. code-block:: bash

   python RestAuth/manage.py testserver --ipv6 RestAuth/fixtures/testserver.json

The ``testserver`` command provides a variety of options, simply run:

.. code-block:: bash

   python RestAuth/manage.py testserver --help

for a comprehensive list.

You might need your own testdata (for example, with some users and/or groups preconfigured), in
which case you have to create a `fixture
<https://docs.djangoproject.com/en/dev/howto/initial-data/>`_. To do this, create a fresh database,
add all necessary data and dump the data to a new fixture:

.. code-block:: bash

   # create empty database:
   python RestAuth/manage.py syncdb --noinput
   python RestAuth/manage.py migrate
   python RestAuth/manage.py flush --noinput

   # create testdata:
   bin/restauth-service.py add --password=foofoo example.com ::1
   bin/restauth-service.py add --password=barbar example.org ::1
   bin/restauth-user.py add --password=example example

   # create fixture:
   python RestAuth/manage.py dumpdata > /path/to/your/library/fixtures/testserver.json

You can then run the testserver with your new fixture by running:

.. code-block:: bash

   python RestAuth/manage.py testserver --ipv6 /path/to/your/library/fixtures/testserver.json
