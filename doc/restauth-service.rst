|bin-restauth-service|
======================

.. only:: man

   Synopsis
   --------

   |bin-restauth-service-bold|  [**-h**] *command* [*option*] ... [*args*] ...

   Description
   -----------

|bin-restauth-service-as-cmd| may be used to manage services that connect to
RestAuth. A service is a system that wants to use RestAuth to store users,
preferences and groups.

RestAuth stores a name (which may not include a ':') and a password that
identify the service. A service has zero or more IPv4 or IPv6 addresses
associated with it, a service can only authenticate from the given adresses,
use the ``*-hosts`` subcommands to manage hosts of a given service. A service
must have permissions to perform the respective actions, use the
``*-permissions`` subcommands to manage permissions for services.

.. only:: homepage

   .. _dist-specific-bin-restauth-service:

   Name of |bin-restauth-service|
   ------------------------------

   If you :doc:`installed from source </install/from-source>`, the script is
   installed as :command:`restauth-service.py`. If you installed RestAuth via
   your distributions package management system, the script is usually called
   :command:`restauth-service`.

Usage
-----

.. only:: html

   .. include:: gen/restauth-service-usage.rst

Use one of the commands (i.e. add, view, ls, ...) to perform the respective operation. Each command
usually requires more arguments to it, see the respective section for arguments (and possible
options) for each command.

.. only:: html

   Getting runtime help
   ^^^^^^^^^^^^^^^^^^^^^^^

   To get an authoritative list of available commands, use:

   .. parsed-literal:: |bin-restauth-service| --help

   If you want more information on a specific comannd, do:

   .. parsed-literal:: |bin-restauth-service| *command* --help

   ... or see the :ref:`service-available-commands` section below.

.. only:: man

    Use "|bin-restauth-service-bold| **--help**" to get an authoritative list of available
    commands. If you want help on a specific command, use
    "|bin-restauth-service-bold| *command* **--help**" or see the
    :ref:`AVAILABLE COMMANDS<service-available-commands>` section below.

Examples
--------

.. example:: |bin-restauth-service-bold| **add** *example.com*

   Add the service *example.com* and prompt for a password.


.. example:: |bin-restauth-service-bold| **add --gen-password** *example.com*

   Add the service *example.com* and print a generated password to stdout.

.. example:: |bin-restauth-service-bold| **ls**

   List all available services.

.. example:: |bin-restauth-service-bold| **view** *example.com*

   View all details of the service *example.com*.

.. example:: |bin-restauth-service-bold| **set-password --password=**\ *foobar* *example.com*

   Set the password of the service *example.com* (which must already exist)
   to *foobar*.

.. example:: |bin-restauth-service-bold| **set-hosts** *example.com* *192.168.0.1* *192.168.0.2*

   Enable the service *example.com* for the hosts *192.168.0.1* *192.168.0.2*.
   Note that this removes any previously configured hosts.

.. example:: |bin-restauth-service-bold| **set-permissions** *example.com* *user\**

   Specify that the service *example.com* is allowed to perform all user operations.

.. example:: |bin-restauth-service-bold| **rm-permissions** *example.com* *user_delete*

   Specify that the service *example.com* is **not** allowed to delete users.

.. example:: |bin-restauth-service-bold| **remove** *example.com*

   Remove the service *example.com* from RestAuth. This will also remove any
   groups defined for the service, see **restauth-groups**\ (1).

A typical workflow for adding a service is:

.. parsed-literal::

   |bin-restauth-service| add example.net
   |bin-restauth-service| set-hosts 127.0.0.1 ::1
   |bin-restauth-service| set-permissions user_verify_password user_change_password

Please see the :ref:`available permissions <service-available-permissions>` below for a full
reference on what permissions can be configured.

.. _service-available-commands:

Available commands
------------------

The following subsections never document the '-h' parameter for clarity.

.. include:: gen/restauth-service-commands.rst

.. _service-available-permissions:

Available permissions
---------------------

A service can have zero or more permissions. There is a permission available for each operation
available via the RestAuth protocol. If a service has no permissions, you will not be able to
perform any operations.

Handling users
^^^^^^^^^^^^^^

.. include:: gen/restauth-service-permissions-users.rst

Handling properties
^^^^^^^^^^^^^^^^^^^

.. include:: gen/restauth-service-permissions-properties.rst

Handling groups
^^^^^^^^^^^^^^^

.. include:: gen/restauth-service-permissions-groups.rst

Influential environment variables
---------------------------------

.. include:: includes/env-variables.rst

.. only:: man

   See Also
   ^^^^^^^^

   :manpage:`restauth-user(1)`, :manpage:`restauth-group(1)`, :manpage:`restauth-import(1)`
