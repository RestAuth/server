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
        :return: True if the password exists, False otherwise.
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
    """todo."""

    def list(self, user):
        raise NotImplementedError

    def create(self, user, key, value, dry=False):
        raise NotImplementedError

    def get(self, user, key):
        raise NotImplementedError

    def set(self, user, key, value):
        raise NotImplementedError

    def set_multiple(self, user, props, dry=False):
        raise NotImplementedError

    def remove(self, user, key):
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
    """todo."""

    def get(self, service, name):
        raise NotImplementedError

    def list(self, service, user=None):
        raise NotImplementedError

    def create(self, service, name, dry=False):
        raise NotImplementedError

    def exists(self, service, name):
        raise NotImplementedError

    def add_user(self, user, group):
        raise NotImplementedError

    def members(self, group, depth=None):
        raise NotImplementedError

    def is_member(self, group, user):
        raise NotImplementedError

    def rm_user(self, group, user):
        raise NotImplementedError

    def add_subgroup(self, group, subgroup):
        raise NotImplementedError

    def subgroups(self, group, filter=True):
        raise NotImplementedError

    def rm_subgroup(self, group, subgroup):
        raise NotImplementedError

    def remove(self, group):
        raise NotImplementedError

    def parents(self, group):
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
