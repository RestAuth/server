|bin-restauth-user|
===================

.. only:: man

   Synopsis
   --------

   |bin-restauth-user-bold| [**-h**] *command* [*option*] ... [*args*] ...

   Description
   -----------

|bin-restauth-user-as-cmd| manages users in RestAuth. Users are clients that
want to authenticate with services that use RestAuth.

Note that |bin-restauth-user-as-cmd| does not enforce restrictions on usernames as
rigorously as the when handling users through the standard interface. Instead,
only characters explicitly forbidden by the protocol specification are blocked.
This way it is easy to handle users (about to be) imported from other systems.

.. only:: homepage

   .. _dist-specific-bin-restauth-user:

   Name of |bin-restauth-user|
   ---------------------------

   If you :doc:`installed from source </install/from-source>`, the script is
   installed as :command:`restauth-user.py`. If you installed RestAuth via
   your distributions package management system, the script is usually called
   :command:`restauth-user`.

Usage
-----

.. only:: html

   .. include:: gen/restauth-user-usage.rst

Use one of the commands (either set-password, verify, list, add, rm or view) to
perform the respective operation. Each command usually requires more arguments
to it, see the respective section for arguments (and possible options) for each
command.

.. only:: html

   Getting runtime help
   ^^^^^^^^^^^^^^^^^^^^^^^

   To get an authoritative list of available commands, use:

   .. parsed-literal:: |bin-restauth-user| --help

   If you want more information on a specific comannd, do:

   .. parsed-literal:: |bin-restauth-user| command --help

   ... or see the :ref:`user-available-commands` section below.

.. only:: man

   Use "|bin-restauth-user-bold| **--help**" to get an authoritative list of
   available commands. If you want help on a specific command, use
   "|bin-restauth-user-bold| *command* **--help**" or see
   the :ref:`AVAILABLE COMMANDS <user-available-commands>` section below.

Examples
--------

.. example:: |bin-restauth-user| **add** *exampleuser*

   Add a user called *exampleuser*. Since neither **-**\ **-password** nor
   **-**\ **-gen-password** was specified, |bin-restauth-user-as-cmd| will
   prompt for a password.

.. example:: |bin-restauth-user| **add -**\ **-gen-password** *exampleuser*

   Add a user called *exampleuser*, automatically generate a password and print
   it to stdout.

.. example:: |bin-restauth-user| **view** *exampleuser*

   View all details of *exampleuser*.

.. example:: |bin-restauth-user| **list**

   List all users known to RestAuth.

.. example:: |bin-restauth-user| **verify -**\ **-password=**\ *foobar exampleuser*

   Verify that *exampleuser* has the password *foobar*.
   |bin-restauth-user-as-cmd| will exit with status code 0 if the password
   matches and 1 if not.

.. example:: |bin-restauth-user| **set-password -**\ **-gen-password** *exampleuser*

   Generate a  new password for *exampleuser*.


.. example:: |bin-restauth-user| **rm** *exampleuser*

   Remove *exampleuser* from RestAuth.

.. _user-available-commands:

Available commands
------------------

The following subsections never document the '-h' parameter for clarity.

.. include:: gen/restauth-user-commands.rst

Influential environment variables
---------------------------------

.. include:: includes/env-variables.rst

.. only:: man

   See Also
   ^^^^^^^^

   :manpage:`restauth-service(1)`, :manpage:`restauth-group(1)`, :manpage:`restauth-import(1)`
