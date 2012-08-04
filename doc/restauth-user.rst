|bin-restauth-user|
===================

.. only:: man

   Synopsis
   --------

   **restauth-user** [**-h**] *command* [*option*] ... [*args*] ...

   Description
   -----------

*restauth-user* manages users in RestAuth. Users are clients that want to authenticate with
services that use RestAuth.

Note that *restauth-user* does not enforce restrictions on usernames as
rigorously as the when handling users through the standard interface. Instead,
only characters explicitly forbidden by the protocol specification are blocked.
This way it is easy to handle users (about to be) imported from other systems.

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

   To get an authoritative list of available commands, use::

      restauth-user --help

   If you want more information on a specific comannd, do::

      restauth-user command --help

   ... or see the :ref:`user-available-commands` section below.

.. only:: man

    Use "**restauth-user --help**" to get an authoritative list of available
    commands. If you want help on a specific command, use "**restauth-user**
    *command* **--help**" or see the
    :ref:`AVAILABLE COMMANDS<user-available-commands>` section below.

Examples
--------

.. example:: **restauth-user add** *exampleuser*

   Add a user called *exampleuser*. Since neither **-**\ **-password** nor
   **-**\ **-gen-password** was specified, **restauth-user** will prompt for a
   password.

.. example:: **restauth-user add -**\ **-gen-password** *exampleuser*

   Add a user called *exampleuser*, automatically generate a password and print
   it to stdout.

.. example:: **restauth-user view** *exampleuser*

   View all details of *exampleuser*.

.. example:: **restauth-user list**

   List all users known to RestAuth.

.. example:: **restauth-user verify -**\ **-password=**\ *foobar exampleuser*

   Verify that *exampleuser* has the password *foobar*.
   **restauth-user** will exit with status code 0 if the password does match or
   1 otherwise.

.. example:: **restauth-user set-password -**\ **-gen-password** *exampleuser*

   Generate a  new password for *exampleuser*.


.. example:: **restauth-user rm** *exampleuser*

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
