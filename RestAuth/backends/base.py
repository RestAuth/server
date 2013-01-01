# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RestAuth.  If not, see <http://www.gnu.org/licenses/>.


class UserInstance(object):
    """Class representing a user.

    Instances of this class should provide the ``username`` and ``id``
    property.

    * The ``username`` is the username of the user as used by the protocol.
    * The ``id`` may be the same as the username or some backend
      specific id, i.e. one that allows faster access.
    """

    def __init__(self, id, username):
        self.id = id
        self.username = username


class GroupInstance(object):
    """Class representing a group.

    Instances of this class should provide the ``name``, ``id`` and ``service``
    properties. For the ``name`` and ``id`` properties, the same semantics as
    for :py:class:`~RestAuth.backends.base.UserInstance` apply.

    The ``service`` property is a service as configured by
    |bin-restauth-service|. Its name is (confusingly!) available as its
    ``username`` property.
    """

    def __init__(self, id, name, service):
        self.id = id
        self.name = name
        self.service = service


class UserBackend(object):
    """Provide the most basic user operations and password management."""

    def get(self, username):
        """Get a user object for the given username.

        This method is used to get user objects passed to property- and
        group-backends.

        :param username: The username.
        :type  username: str
        :return: A user object providing at least the properties of the
            UserInstance class.
        :rtype: :py:class:`~.UserInstance`
        :raise: :py:class:`~RestAuth.common.errors.UserNotFound` if the user
            doesn't exist.
        """
        raise NotImplementedError

    def list(self):
        """Get a list of all usernames.

        Each element of the returned list should be a valid username that can
        be passed to :py:meth:`~.UserBackend.get`.

        :return: A list of usernames.
        :rtype: list
        """
        raise NotImplementedError

    def create(self, username, password=None, properties=None,
               property_backend=None, dry=False):
        """Create a new user.

        The ``username`` is already validated, so you don't need to do any
        additional validation here. If your backend has username restrictions,
        please implement a :ref:`username validator <implement-validators>`.

        If ``properties`` are passed, please use the property backend passed to
        store the properties:

        .. code-block:: python

           user = ...  # create the user
           property_backend.set_multiple(user, properties, dry=dry)
           return user

        The ``dry`` parameter tells you if you should actually create the user.
        The parameter will be True for `dry-runs
        <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal
        invocation but shouldn't actually create the user.

        :param username: The username.
        :type  username: str
        :param password: The password to set. If not given, the user should
            not have a valid password and is unable to log in.
        :type  password: str
        :param properties: Any initial properties for the user.
        :type  properties: dict
        :param property_backend: The backend to use to store properties.
        :type  property_backend: :py:class:`~.PropertyBackend`
        :param dry: Wether or not to actually create the user.
        :type  dry: boolean
        :return: A user object providing at least the properties of the
            UserInstance class.
        :rtype: :py:class:`~.UserInstance`
        :raise: :py:class:`~RestAuth.common.errors.UserExists` if the user
            already exist.
        """
        raise NotImplementedError

    def exists(self, username):
        """Determine if the username exists.

        :param username: The username.
        :type  username: str
        :return: True if the user exists, False otherwise.
        :rtype: boolean
        """
        raise NotImplementedError

    def check_password(self, username, password):
        """Check a users password.

        :param username: The username.
        :type  username: str
        :param password: The password to check.
        :type  password: str
        :return: True if the password is correct, False otherwise.
        :rtype: boolean
        :raise: :py:class:`~RestAuth.common.errors.UserNotFound` if the user
            doesn't exist.
        """
        raise NotImplementedError

    def set_password(self, username, password=None):
        """Set a new password.

        :param username: The username.
        :type  username: str
        :param password: The new password. If None or empty, the user should
            get an unusable password.
        :type  password: str
        :raise: :py:class:`~RestAuth.common.errors.UserNotFound` if the user
            doesn't exist.
        """
        raise NotImplementedError

    def remove(self, username):
        """Remove a user.

        :param username: The username.
        :type  username: str
        :raise: :py:class:`~RestAuth.common.errors.UserNotFound` if the user
            doesn't exist.
        """
        raise NotImplementedError

    def testSetUp(self):
        """Set up your backend for a test run.

        This method is exclusively used in unit tests. It should perform any
        actions necessary to start a unit test.

        .. NOTE:: You do not need to implement this method, if there is nothing
           to do.
        """
        pass

    def testTearDown(self):
        """Tear down your backend after a test run.

        This method is exclusively used in unit tests. It should perform any
        actions necessary after a unit test. In general, this should completely
        wipe all users created during a unit test.

        .. NOTE:: You do not need to implement this method if the backend
           automatically cleans itself.
        """
        pass


class PropertyBackend(object):
    """Provide user properties."""

    def list(self, user):
        """Get a full list of all user properties.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`~.UserInstance`
        :return: A dictionary of key/value pairs, each describing a property.
        :rtype: dict
        """
        raise NotImplementedError

    def create(self, user, key, value, dry=False):
        """Create a new user property.

        This method should return
        :py:class:`~RestAuth.common.errors.PropertyExists` if a property with
        the given key already exists.

        The ``dry`` parameter tells you if you should actually create the
        property.  The parameter will be True for `dry-runs
        <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal
        invocation but shouldn't actually create the property.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`~.UserInstance`
        :param key: The key identifying the property.
        :type  key: str
        :param value: The value of the property.
        :type  value: str
        :param dry: Wether or not to actually create the property.
        :type  dry: boolean
        :return: A tuple of key/value as they are stored in the database.
        :rtype: tuple
        :raise: :py:class:`~RestAuth.common.errors.PropertyExists` if the
            property already exists.
        """
        raise NotImplementedError

    def get(self, user, key):
        """Get a specific property of the user.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`~.UserInstance`
        :param  key: The key identifying the property.
        :type   key: str
        :return: The value of the property.
        :rtype: str
        :raise: :py:class:`RestAuth.common.errors.PropertyNotFound` if the
            property doesn't exist.
        """
        raise NotImplementedError

    def set(self, user, key, value, dry=False):
        """Set a property for the given user.

        Unlike :py:meth:`~.PropertyBackend.create` this method overwrites an
        existing property.

        The ``dry`` parameter is never passed by RestAuth itself. You may pass
        the parameter when calling this method using :py:meth:`.set_multiple`.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`~.UserInstance`
        :param key: The key identifying the property.
        :type  key: str
        :param value: The value of the property.
        :type  value: str
        :return: A tuple of key/value as they are stored in the database.
            The value should be ``None`` if the property didn't exist
            previously or the old value, if it did.
        :rtype: tuple
        """
        raise NotImplementedError

    def set_multiple(self, user, props, dry=False):
        """Set multiple properties at once.

        This method may just call :py:meth:`~.PropertyBackend.set` multiple
        times. Some backends have faster methods for setting multiple
        values at once, though.

        The ``dry`` parameter tells you if you should actually create the
        properties. The parameter will be True for `dry-runs
        <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal
        invocation but shouldn't actually create the properties.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`~.UserInstance`
        :param dry: Wether or not to actually create the properties.
        :type  dry: boolean
        """
        raise NotImplementedError

    def remove(self, user, key):
        """Remove a property.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`~.UserInstance`
        :param key: The key identifying the property.
        :type  key: str
        :raise: :py:class:`RestAuth.common.errors.PropertyNotFound` if the
            property doesn't exist.
        """
        raise NotImplementedError

    def testSetUp(self):
        """Set up your backend for a test run.

        This method is exclusively used in unit tests. It should perform any
        actions necessary to start a unit test.

        .. NOTE:: You do not need to implement this method, if there is nothing
           to do.
        """
        pass

    def testTearDown(self):
        """Tear down your backend after a test run.

        This method is exclusively used in unit tests. It should perform any
        actions necessary after a unit test. In general, this should completely
        wipe all users and properties created during a unit test.

        .. NOTE:: You do not need to implement this method if the backend
           automatically cleans itself.
        """
        pass


class GroupBackend(object):
    """Provide groups.

    A group may be identified by its name and a service.  The ``service``
    parameter passed in many methods is an instance of
    `django.contrib.auth.models.User
    <https://docs.djangoproject.com/en/dev/ref/contrib/auth/#django.contrib.auth.models.User>`_.
    If a :py:class:`.GroupInstance` is passed (or returned), the groups service
    is/should be available as the ``service`` property.
    """

    def get(self, service, name):
        """Get a group object representing the given group.

        :param service: The service of the named group.
        :param    name: The name of the group.
        :type     name: str
        :return: A group object providing at least the properties of the
            GroupInstance class.
        :rtype: :py:class:`.GroupInstance`
        :raises: :py:class:`RestAuth.common.errors.GroupNotFound` if the named
            group does not exist.
        """
        raise NotImplementedError

    def list(self, service, user=None):
        """Get a list of group names for the given service.

        :param service: The service of the named group.
        :param    user: If given, only return groups that the user is a member
            of.
        :type     user: :py:class:`.UserInstance`
        :return: list of strings, each representing a group name.
        :rtype: list
        """
        raise NotImplementedError

    def create(self, service, name, dry=False):
        """Create a new group for the given service.

        The ``dry`` parameter tells you if you should actually create the
        group. The parameter will be True for `dry-runs
        <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal
        invocation but shouldn't actually create the group.

        :param service: The service of the named group.
        :param    name: The name of the group.
        :type     name: str
        :param     dry: Wether or not to actually create the group.
        :type      dry: boolean
        :return: A group object providing at least the properties of the
            GroupInstance class.
        :rtype: :py:class:`.GroupInstance`
        :raises: :py:class:`RestAuth.common.errors.GroupExists` if the group
            already exists.
        """
        raise NotImplementedError

    def exists(self, service, name):
        """Determine if a group exists for the given service.

        :param service: The service of the named group.
        :param    name: The name of the group.
        :type     name: str
        :return: True if the group exists, False otherwise.
        :rtype: boolean
        """
        raise NotImplementedError

    def add_user(self, group, user):
        """Add a user to the given group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type   user: :py:class:`.UserInstance`
        """
        raise NotImplementedError

    def members(self, group, depth=None):
        """Get a list of all members of this group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param depth: Override the recursion depth to use for meta-groups.
            Normally, the backend should use :setting:`GROUP_RECURSION_DEPTH`.
        :type  depth: int
        :return: list of strings, each representing a username
        :rtype: list
        """
        raise NotImplementedError

    def is_member(self, group, user):
        """Determine if a user is a member of the given group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param  user: A user as returned by :py:meth:`.UserBackend.get`.
        :type   user: :py:class:`.UserInstance`
        :return: True if the User is a member, False otherwise
        :rtype: boolean
        """
        raise NotImplementedError

    def rm_user(self, group, user):
        """Remove a user from the group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param  user: A user as returned by :py:meth:`.UserBackend.get`.
        :type   user: :py:class:`.UserInstance`
        :raises: :py:class:`RestAuth.common.errors.UserNotFound` if the user
            is not a member of the group.
        """
        raise NotImplementedError

    def add_subgroup(self, group, subgroup):
        """Make a group a subgroup of another group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param subgroup: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  subgroup: :py:class:`.GroupInstance`
        """
        raise NotImplementedError

    def subgroups(self, group, filter=True):
        """Get a list of subgroups.

        If ``filter=True``, the method should only return groups that belong to
        the same service as the given group. The returned list should be a list
        of strings, each representing a groupname.

        If ``filter=False``, the method should return all groups, regardless of
        their service. The list should contain :py:class:`.GroupInstance`
        objects.

        .. NOTE:: The filter argument is only False when called by some
            command line scripts.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param filter: Wether or not to filter for the groups service. See
            description for a detailled explanation.
        :type  filter: boolean
        :return: A list of subgroups.
        """
        raise NotImplementedError

    def rm_subgroup(self, group, subgroup):
        """Remove a subgroup from a group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param subgroup: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  subgroup: :py:class:`.GroupInstance`
        :raises: :py:class:`RestAuth.common.errors.GroupNotFound` if the
            named subgroup is not actually a subgroup of group.
        """
        raise NotImplementedError

    def remove(self, service, name):
        """Remove a group.

        :param service: The service of the named group.
        :param    name: The name of the group.
        :type     name: str
        :raises: :py:class:`RestAuth.common.errors.GroupNotFound` if the named
            group does not exist.
        """
        raise NotImplementedError

    def parents(self, group):
        """Get a list of all parent groups of a group.

        This method is only used by some command-line scripts.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :return: List of parent groups, each being a GroupInstance object.
        :rtype: list
        """
        raise NotImplementedError

    def testSetUp(self):
        """Set up your backend for a test run.

        This method is exclusively used in unit tests. It should perform any
        actions necessary to start a unit test.

        .. NOTE:: You do not need to implement this method, if there is nothing
           to do.
        """
        pass

    def testTearDown(self):
        """Tear down your backend after a test run.

        This method is exclusively used in unit tests. It should perform any
        actions necessary after a unit test. In general, this should completely
        wipe all users and groups created during a unit test.

        .. NOTE:: You do not need to implement this method if the backend
           automatically cleans itself.
        """
        pass
