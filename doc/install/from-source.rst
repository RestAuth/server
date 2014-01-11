Installation from source
========================

Requirements
------------

RestAuth has the following requirements:

* `Python`_ 2.6.5 or later or Python 3.2 or later
* `Django`_ 1.6 or later - RestAuth is written as a Django project
* Any database supported by Django, that supports transactions, see the
  `DATABASES`_ setting.
* `RestAuthCommon`_ 0.6.2 or later
* :pypi:`mimeparse` 0.1.4 or later
* The `argparse`_ module ships with Python 2.7 and is available for Python 2.6
* `Django South`_ is used for handeling schema migrations.

Additionally, various optional features require additional libraries:

* :pypi:`MySQL-python` if you use MySQL as a :setting:`DATABASES` backend.
* :pypi:`redis` and :pypi:`hiredis` if you want to use the
  :py:class:`~backends.redis_backend.RedisPropertyBackend` or use a Redis
  instance as a cache backend.
* :pypi:`django-hashers-passlib` (>= 0.1) and :pypi:`passlib` (>= 0.6.2) if you want to
  use most of the :doc:`custom password hashers </config/custom-hashes>`.

Get source
----------

From git
++++++++

This project is developed `on GitHub <git_>`_. To clone the repository into the
:file:`RestAuth` directory, simply do:

.. code-block:: bash

   git clone https://github.com/RestAuth/server.git RestAuth

Older versions are marked as tags. You can view available tags with
:command:`git tag -l`. You can use any of those versions with :command:`git
checkout`, for example :command:`git checkout 0.6.3`.  To move back to the newest
version, use :command:`git checkout master`.

If you ever want to update the source code, just use:

.. code-block:: bash

   python setup.py clean
   git pull origin master

... and do the same as if you where
:ref:`doing a new installation <install_from-source_installation>`.

Official releases
+++++++++++++++++

You can download official releases of RestAuth `here <download-releases_>`_. The
latest release is version |restauth-latest-release|.

.. _install_from-source_installation:

Installation
------------

Installation itself is very easy. Just go to the directory where your source is
located (:file:`RestAuth` in the above example) and run:

.. code-block:: bash

   python setup.py build
   python setup.py install

Once you have installed RestAuth, you can go on :doc:`configuring your webserver
<../config/webserver>` and :doc:`configuring RestAuth <../config/restauth>`.

Next steps
----------
Now that you have installed RestAuth, you still need to

#. :doc:`configure your webserver <../config/webserver>`
#. :doc:`setup your database <../config/database>`
#. :doc:`configure RestAuth <../config/restauth>`

Run tests
---------

RestAuth features an extensive test suite. You can run those tests using:

.. code-block:: bash

   python setup.py test

Note that you can run these tests even if you already installed RestAuth or
locally configured your RestAuth installation. The tests will *always* use their
own temporary database.

Build documentation
-------------------

To generate the most recent documentation (the newest version of the document
you're currently reading), just run:

.. code-block:: bash

   python setup.py build_doc

.. NOTE:: You can build documentation customized for a specific distribution
   with:

   .. code-block:: bash

      python setup.py build_doc -t debian

   This will customize various paths, binary names etc. for what is used in the
   respective distribution.

.. _source-update:

Updating the source
-------------------

To update the source code, just run:

.. code-block:: bash

   python setup.py clean
   git pull
   python setup.py install

After you updated the source, don't forget to :ref:`update your database schema
<update-database>` and :ref:`check for new settings <update-settings>`.
