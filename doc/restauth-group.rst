|bin-restauth-group|
====================

.. only:: man

   Synopsis
   --------

   **restauth-group** [**-h**] *command* [*option*] ... [*args*] ...

   Description
   -----------

|bin-restauth-group-bold| manages groups in RestAuth. Groups are a powerful but simple way for managing
permissions. A user can be a member in one or more groups, which grants her/him certain rights.
Analogous concepts are used on many systems, such as Unix and Windows systems and most content
management systems.

A group may itself also be a member of one or more groups, making it the **subgroup** of the groups
of which it is a member, which are in turn called **metagroups**. A subgroup automatically inherits
all memberships from all metagroups. This way you can easily grant users multiple memberships at
once.

A group is associated with at most one service that uses RestAuth. A service can only see the groups
associated with it. If a group is not associated with any service, the group can not be seen by
any service, the only way to modify them is via this script.

Note that a group can be a member of any other group, even it is associated with a different
service or none at all. A common use-case would be to have a metagroup called *admin* that is either
not associated with any service or with some central management service. Any other services using
RestAuth have their own *admin* group (which can each have a different name, whatever suits the
service best), which are subgroups to the global admin group. 


Usage
-----

.. only:: html
   
   .. include:: gen/restauth-group-usage.rst

Use one of the commands (either add, add-group, add-user, list, rm, rm-group, rm-user or view) to
perform the respective operation. Each command usually requires more arguments
to it, see the respective section for arguments (and possible options) for each
command.


.. only:: html

   Getting runtime help
   ^^^^^^^^^^^^^^^^^^^^^^^

   To get an authoritative list of available commands, use:
      
   .. parsed-literal:: |bin-restauth-group| --help

   If you want more information on a specific comannd, do:
   
   .. parsed-literal:: |bin-restauth-group| <command> --help
   
   ... or see the :ref:`group-available-commands` section below.

.. only:: man

    Use "**restauth-group --help**" to get an authoritative list of available
    commands. If you want help on a specific command, use "**restauth-group** 
    *command* **--help**" or see the 
    :ref:`AVAILABLE COMMANDS<group-available-commands>` section below.

Examples
--------

.. example:: |bin-restauth-group-bold| **add** *global_admin_group*

   Create a group called *global_admin_group* that is not associated with any service.
   
.. example:: |bin-restauth-group-bold| **add --service=**\ *example.com* *local_admin_group*

   Create a group called *local_admin_group* that is associated with the service called *example.com*.
   
.. example:: |bin-restauth-group-bold| *view** *global_admin_group*

   View all details of the group *global_admin_group*.
   
.. example:: |bin-restauth-group-bold| **ls**

   List all groups not associated with any service.
   
.. example:: |bin-restauth-group-bold| **ls --service=**\ *example.com*

   List all groups associated with the service *example.com*.
   
.. example:: |bin-restauth-group-bold| **add-user** *global_admin_group* *admin_user*

   Add *admin_user* to the *global_admin_group* group.

.. example:: |bin-restauth-group-bold| **add-user --service=**\ *example.com* *local_admin_group* *local_admin*

   Add *local_admin* to the *local_admin_group* group.   
   
.. example:: |bin-restauth-group-bold| **add-group --sub-service=**\ *example.com* *global_admin_group* *local_admin_group*

   Make the group *local_admin_group* a member of the *global_admin_group*. Any user that is a
   member of the latter is now automatically a member of the former.

.. example:: |bin-restauth-group-bold| **rm-group --sub-group=**\ *example.com* *global_admin_group* *local_admin_group*

   Remove *local_admin_group*'s membership in the *global_admin_group*.
   
.. example:: |bin-restauth-group-bold| **rm-user** *global_admin_group* *admin_user*

   Remove the membership of the user *admin_user* from the group *global_admin_group*.

.. example:: |bin-restauth-group-bold| **rm** *global_admin_group*

   Remove the group *global_admin_group*.

.. _group-available-commands:

Available commands
------------------

The following subsections never document the '-h' parameter for clarity.

.. include:: gen/restauth-group-commands.rst

Influential environment variables
---------------------------------

.. include:: includes/env-variables.rst

.. only:: man

   See Also
   ^^^^^^^^

   :manpage:`restauth-service(1)`, :manpage:`restauth-user(1)`, :manpage:`restauth-import(1)`
