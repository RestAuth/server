Backends
========

RestAuth uses backends to store data. RestAuth knows three different types of
backends:

:ref:`user-backends`
   Store user data.
:ref:`property-backends`
   Store user properties.
:ref:`group-backends`
   Store groups.

RestAuth can use different backends for each individual task, but property- and
group-backends may depend on a specific user-backend being used. Most
prominently, the default backends
:py:class:`~RestAuth.backends.django_orm.DjangoPropertyBackend` and
:py:class:`~RestAuth.backends.django_orm.DjangoGroupBackend` require that you
also use :py:class:`~RestAuth.backends.django_orm.DjangoUserBackend`.

Configuring backends
____________________

To configure what backend to use, use the :setting:`USER_BACKEND`,
:setting:`PROPERTY_BACKEND` and :setting:`GROUP_BACKEND` settings. Backends
shipping with RestAuth are listed below, if you want to develop your own
backend(s), please see :ref:`developing-backends`.

Note that each backend may use settings not listed in the
:doc:`settings reference </config/all-config-values>`. For backend-specific
settings, please consult the backends documentation.

.. _user-backends:

User backends
_____________

A user backend handles the most basic operations related to users. The user
backend is used to create and delete users as well as to check and update a
users password.

.. autoclass:: RestAuth.backends.django_orm.DjangoUserBackend

.. _property-backends:

Property backends
_________________

A property backend handles user properties such as email, full
name and so on.

.. autoclass:: RestAuth.backends.django_orm.DjangoPropertyBackend

.. autoclass:: RestAuth.backends.redis_backend.RedisPropertyBackend

.. _group-backends:

Group backends
______________

A group backend handles user groups. Groups may be used by a service for
authorization or similar purposes.

.. autoclass:: RestAuth.backends.django_orm.DjangoGroupBackend

.. _developing-backends:

Developing your own backend
___________________________

.. autoclass:: RestAuth.backends.base.UserBackend
   :members:

.. autoclass:: RestAuth.backends.base.PropertyBackend
   :members:

.. autoclass:: RestAuth.backends.base.GroupBackend
   :members:

Returning User/Group objects
++++++++++++++++++++++++++++

Some backend methods to implement expect (or return) a user/group object. The
objects don't have to be of any particular class but must have a few properties
available. The classes below are given for convenience only, if your objects
already provide the correct properties, there is no need to use them.

.. autoclass:: RestAuth.backends.base.UserInstance
.. autoclass:: RestAuth.backends.base.GroupInstance
