Manage a RestAuth server
========================

Once you have :doc:`configured your database </config/database>`, you can start managing your
RestAuth server. RestAuth tries not to cause a lot of maintenance, but some is still necessary.

Services
--------

Services are systems (like a CMS, a Wiki, a Linux installation) that want to use RestAuth. The
degree to which they use RestAuth is entirely up to the application, some systems do not use groups
and/or preferences at all.

For a service to be able to use RestAuth, you need to define shared credentials and tell RestAuth
from which locations it will connect. We provide one command-line script to do that:

.. toctree::
   :maxdepth: 1
   
   /restauth-service

Users and groups
----------------

Users may be managed entirely by a client application. For consistency and for ease of management
we also provide a command-line tool to manage users directly on the RestAuth server:

.. toctree::
   :maxdepth: 1
   
   /restauth-user

Users may be a member to one or more groups. Unlike users, groups are always specific to the service
using it. Additionally groups may be global groups, which are not directly visible to any service.
Groups may also inherit memberships from a parent group.

.. toctree::
   :maxdepth: 1
   
   /restauth-group
   
Subgroups and global groups
+++++++++++++++++++++++++++

The usefulness of subgroups and global groups may not be immediately apparent. It is however a
powerful concept to manage permissions.

One common scenario is to collect all users that should (not) have a certain privilege in several
systems in one central group. This group can either be global (meaning it does not belong to any
service, and is only manageable with :doc:`/restauth-group`) or belong to a service from which you
want to manage that particular group.

The next logical step is make other groups subgroups of that common group, these groups are then
used by the services to grant users the specific permission. This scenario enables you to easily
and centrally manage who gets a certain permission in your system and who does not. You are even
still able to grant that permission on a per-service basis if you make a user only a member of one
(or more) of the subgroups.

.. _manage_advanced:

Advanced management
-------------------

RestAuth is set up as a Django project. As such, it also features a `manage.py
<https://docs.djangoproject.com/en/dev/ref/django-admin/>`_. The source installation installs the
script together with the source code. Most distributions install the script as

.. toctree::
   :maxdepth: 1
   
   /bin/restauth-manage

Migrating data from existing services
-------------------------------------

Migrating users, groups and preferences from your services to RestAuth is easy. There is a
:doc:`import data format </migrate/import-format>` that can be used by :doc:`/restauth-import`. All
you need to do is get your service to produce data in this format. Some client plugins already
provide helpers for that.

We also collect solutions we know of in the :doc:`migration overview </migrate/overview>`.