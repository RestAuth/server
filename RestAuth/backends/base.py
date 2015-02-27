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

from __future__ import unicode_literals, absolute_import

from django.utils import importlib
from django.utils.module_loading import import_string


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

    def __lt__(self, other):  # pragma: py3
        return self.username < other.username


class GroupInstance(object):
    """Class representing a group.

    Instances of this class should provide the ``name``, ``id`` and ``service``
    properties. For the ``name`` and ``id`` properties, the same semantics as
    for :py:class:`~backends.base.UserInstance` apply.

    The ``service`` property is a service as configured by
    |bin-restauth-service|. Its name is (confusingly!) available as its
    ``username`` property.
    """

    def __init__(self, id, name, service):
        self.id = id
        self.name = name
        self.service = service

    def __lt__(self, other):  # pragma: py3
        return self.username < other.username


class TransactionContextManager(object):
    def __init__(self, backend, dry=False):
        self.backend = backend
        self.dry = dry

    def __enter__(self):
        self.init = self.backend.init_transaction()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None and self.dry is False:
            self.backend.commit_transaction(transaction_id=self.init)
        else:
            self.backend.rollback_transaction(transaction_id=self.init)

class BackendBase(object):
    _library = None
    library = None

    def _load_library(self):
        if self._library is not None:
            return self._library

        if self.library is None:
            raise ValueError("%r: No library attribute specified" % self.__class__.__name__)

        if isinstance(self.library, (tuple, list)):
            name, mod_path = self.library
        else:
            mod_path = self.library

        try:
            self._library = importlib.import_module(mod_path)
            return self._library
        except ImportError as e:
            raise ValueError("Couldn't load %r: %s" % (self.__class__.__name__, e))

    def testSetUp(self):
        """Set up your backend for a test run.

        This method is exclusively used in unit tests. It should perform any actions necessary to
        start a unit test.
        """
        pass

    def testTearDown(self):
        """Tear down your backend after a test run.

        This method is exclusively used in unit tests. It should perform any actions necessary
        after a unit test. In general, this should completely wipe all users created during a unit
        test.
        """
        pass

    def create_user(self, username, password=None, properties=None, groups=None, dry=False):
        """Create a new user.

        The ``username`` is already validated, so you don't need to do any additional validation
        here. If your backend has username restrictions, please implement a :ref:`username
        validator <implement-validators>`.

        The ``dry`` parameter tells you if you should actually create the user. The parameter will
        be True for `dry-runs <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal invocation but
        shouldn't actually create the user.

        :param   username: The username.
        :type    username: str
        :param   password: The password to set. If not given, the user should not have a valid
            password and is unable to log in.
        :type    password: str
        :param properties: An initial set of properties.
        :type  properties: dict
        :param     groups: An inital set of groups.
        :type      groups: list
        :param        dry: Wether or not to actually create the user.
        :type         dry: boolean
        :return: A user object providing at least the properties of the UserInstance class.
        :rtype: :py:class:`~.UserInstance`
        :raise: :py:class:`~common.errors.UserExists` if the user already exist.
        """
        raise NotImplementedError

    def list_users(self):
        """Get a list of all usernames.

        Each element of the returned list should be a valid username that can
        be passed to :py:meth:`~.UserBackend.get`.

        :return: A list of usernames.
        :rtype: list
        """
        raise NotImplementedError

    def user_exists(self, username):
        """Determine if the username exists.

        :param username: The username.
        :type  username: str
        :return: True if the user exists, False otherwise.
        :rtype: boolean
        """
        raise NotImplementedError

    def rename_user(self, username, name):
        """Rename a user.

        This operation is only available via |bin-restauth-user-doc|.

        :param username: The username.
        :type  username: str
        :param     name: The new username.
        :type      name: str
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        :raise: :py:class:`~common.errors.UserExists` if the user already exist.
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
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_password(self, username, password=None):
        """Set a new password.

        :param username: The username.
        :type  username: str
        :param password: The new password. If None or empty, the user should get an unusable
            password.
        :type  password: str
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_password_hash(self, algorithm, hash):
        """Set a users password hash.

        This method is called by |bin-restauth-import| if users with a password hash should be
        imported.

        If you can store password hashes as an arbitrary string and then use Djangos password
        hashing framework for verifying those hashes, you can import the hash like this::

            from common.hashers import import_hash
            django_hash = import_hash(algorithm, hash)

        :param algorithm: The algorithm used for creating the hash.
        :type  algorithm: str
        :param      hash: The hash created by the algorithm.
        :type       hash: str
        """
        raise NotImplementedError

    def remove_user(self, username):
        """Remove a user.

        :param username: The username.
        :type  username: str
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def list_properties(self, username):
        """Get a full list of all user properties.

        :param username: The username.
        :type  username: str
        :return: A dictionary of key/value pairs, each describing a property.
        :rtype: dict
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def create_property(self, user, key, value, dry=False):
        """Create a new user property.

        This method should return :py:class:`~common.errors.PropertyExists` if a property with the
        given key already exists.

        The ``dry`` parameter tells you if you should actually create the property. The parameter
        will be True for `dry-runs <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal invocation but
        shouldn't actually create the property.

        :param username: The username.
        :type  username: str
        :param key: The key identifying the property.
        :type  key: str
        :param value: The value of the property.
        :type  value: str
        :param dry: Wether or not to actually create the property.
        :type  dry: boolean
        :rtype: tuple
        :raise: :py:class:`~common.errors.PropertyExists` if the property already exists.
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def get_property(self, username, key):
        """Get a specific property of the user.

        :param username: The username.
        :type  username: str
        :param key: The key identifying the property.
        :type  key: str
        :return: The value of the property.
        :rtype: str
        :raise: :py:class:`common.errors.PropertyNotFound` if the property doesn't exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_property(self, username, key, value):
        """Set a property for the given user.

        Unlike :py:meth:`~.PropertyBackend.create` this method overwrites an existing property.

        :param username: The username.
        :type  username: str
        :param key: The key identifying the property.
        :type  key: str
        :param value: The value of the property.
        :type  value: str
        :return: ``None`` if the property didn't exist previously or the old value, if it did.
        :rtype: str or None
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_multiple_properties(self, username, properties):
        """Set multiple properties at once.

        This method may just call :py:meth:`~.PropertyBackend.set` multiple times. Some backends
        have faster methods for setting multiple values at once, though.

        :param username: The username.
        :type  username: str
        :param properties: A dictionary of properties.
        :type  properties: dict
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def remove_property(self, username, key):
        """Remove a property.

        :param username: The username.
        :type  username: str
        :param key: The key identifying the property.
        :type  key: str
        :raise: :py:class:`common.errors.PropertyNotFound` if the property doesn't exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def list_groups(self, service, username=None):
        """Get a list of group names for the given service.

        :param service: The service of the named group.
        :param username: If given, only return groups that the user is a member of.
        :type  username: str
        :return: list of strings, each representing a group name.
        :rtype: list
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def create_group(self, name, service=None, users=None, dry=False):
        """Create a new group for the given service.

        The ``dry`` parameter tells you if you should actually create the group. The parameter will
        be True for `dry-runs <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a
        dry-run, the method should behave as closely as possible to a normal invocation but
        shouldn't actually create the group.

        :param name: The name of the group.
        :type  name: str
        :param service: The service of the named group. If None, the group should not belong to any
            service.
        :type  service: :py:class:`~Services.models.Service` or None
        :param users: A list of usernames.
        :type  users: list
        :param dry: Wether or not to actually create the group.
        :type  dry: boolean
        :return: A group object providing at least the properties of the GroupInstance class.
        :rtype: :py:class:`.GroupInstance`
        :raise: :py:class:`common.errors.GroupExists` if the group already exists.
        :raise: :py:class:`~common.errors.UserNotFound` if any of the given users don't exist.
        """
        raise NotImplementedError

    def rename_group(self, name, new_name, service=None):
        """Rename a group.

        This operation is only available via |bin-restauth-group-doc|.

        :param name: The old name of the group.
        :type  name: str
        :param new_name: The new name of the group.
        :type  new_name: str
        :param service: The service of the group.
        :type  service: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`~common.errors.GroupNotFound` if the old group does not exist.
        :raise: :py:class:`~common.errors.GroupExists` if the group already exist.
        """
        raise NotImplementedError

    def set_group_service(self, name, service=None, new_service=None):
        """Set the service of a group.

        This operation is only available via |bin-restauth-group-doc|.

        :param name: The name of the group.
        :type  name: str
        :param service: The old service of the group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param new_service: The new service of the group.
        :type  new_service: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`~common.errors.GroupNotFound` if the old group does not exist.
        :raise: :py:class:`~common.errors.GroupExists` if the new group already exist.
        """
        raise NotImplementedError

    def group_exists(self, name, service=None):
        """Determine if a group exists for the given service.

        :param    name: The name of the group.
        :type     name: str
        :param service: The service of the group to query.
        :type  service: :py:class:`~Services.models.Service` or None
        :return: True if the group exists, False otherwise.
        :rtype: boolean
        """
        raise NotImplementedError

    def set_groups_for_user(self, user, service, groups):
        """Set groups for a user.

        :param user: A user as returned by :py:meth:`.UserBackend.get`.
        :type  user: :py:class:`.UserInstance`
        :param service: The service of all groups to add to.
        :type  service: :py:class:`~Services.models.Service` or None
        :param groups: A list of groupnames. Groups that don't exist have to be created.
        :type  groups: list of str
        :raise: :py:class:`~common.errors.UserNotFound` if the user does not exist.
        """
        raise NotImplementedError

    def set_users_for_group(self, group, service, users):
        """Set all members of a group.

        This method replaces the current list of members with the one passed by ``users``. If a
        user is member of a meta-group, this method must not remove that membership if the user is
        not in the new list of members.

        :param group: A group to set the users for.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param users: A list of usernames.
        :type  users: list
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        :raise: :py:class:`~common.errors.UserNotFound` if any of the users do not exist.
        """
        raise NotImplementedError

    def add_user(self, group, service, user):
        """Add a user to the given group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param user: The user to add.
        :type  user: str
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the named user does not exist.
        """
        raise NotImplementedError

    def members(self, group, service, depth=None):
        """Get a list of all members of this group.

        :param group: The group to get the members for.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param depth: Override the recursion depth to use for meta-groups.  Normally, the backend
            should use :setting:`GROUP_RECURSION_DEPTH`.
        :type  depth: int
        :return: list of strings, each representing a username
        :rtype: list
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        """
        raise NotImplementedError

    def is_member(self, group, service, user):
        """Determine if a user is a member of the given group.

        :param group: The group to test for membersship.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param user: The user to test for membership.
        :type  user: str
        :return: True if the User is a member, False otherwise
        :rtype: boolean
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the named user does not exist.
        """
        raise NotImplementedError


class RestAuthBackend(object):  # pragma: no cover
    """Base class for all RestAuth data backends.

    ``RestAuthBackend`` provides the ``_load_library`` method that allows
    loading python modules upon first use. This is useful if you want to
    implement a backend that uses third-party libraries and do not want to
    cause immediate ImportErrors every time the module is loaded.

    To use this featurr, simply set the ``library`` class attribute and use
    ``self.load_library()`` to load the module into the methods namespace.

    Example::

        from backends.base import UserBackend

        class MyCustomBackend(UserBackend):
            library = 'redis'

            def get(self, username):
                redis = self._load_library()

                # use the redis module...
    """

    _library = None
    library = None

    _group_backend = None

    @property
    def group_backend(self):
        if self._group_backend is None:
            self._group_backend = import_string('backends.group_backend')
        return self._group_backend

    def _load_library(self):
        """Load a library.

        This method is almost a 100% copy from Djangos
        ``django.contrib.auth.hashers.BasePasswordHasher._load_library()``.
        """
        if self._library is not None:
            return self._library
        elif self.library is not None:
            if isinstance(self.library, (tuple, list)):
                name, mod_path = self.library
            else:
                name = mod_path = self.library
            try:
                module = importlib.import_module(mod_path)
            except ImportError:
                raise ValueError("Couldn't load %s backend library" % name)
            return module
        raise ValueError("Hasher '%s' doesn't specify a library attribute" %
                         self.__class__)

    def transaction(self):
        """Override if your backend requires its own transaction management.

        The default will call :py:meth:`~.RestAuthBackend.init_transaction` upon entering a
        transaction, :py:meth:`~.RestAuthBackend.commit_transaction` upon success and
        :py:meth:`~.RestAuthBackend.rollback_transaction` upon error.
        """
        return TransactionContextManager(self)

    def init_transaction(self):
        """Start a transaction.

        If the transaction handling of your backend provides a transaction id required for
        commit/rollback, simply return it and commit_transaction/rollback_transaction will receive
        it as keword argument.
        """
        pass

    def commit_transaction(self, transaction_id=None):
        """Commit a transaction."""
        pass

    def rollback_transaction(self, transaction_id=None):
        """Rollback a transaction."""
        pass

    def testSetUp(self):
        """Set up your backend for a test run.

        This method is exclusively used in unit tests. It should perform any actions necessary to
        start a unit test.
        """
        pass

    def testTearDown(self):
        """Tear down your backend after a test run.

        This method is exclusively used in unit tests. It should perform any actions necessary
        after a unit test. In general, this should completely wipe all users created during a unit
        test.
        """
        pass


class GroupBackend(RestAuthBackend):  # pragma: no cover
    """Provide groups.

    A group may be identified by its name and a service.  The ``service`` parameter passed in many
    methods is an instance of `django.contrib.auth.models.User
    <https://docs.djangoproject.com/en/dev/ref/contrib/auth/#django.contrib.auth.models.User>`_.
    If a :py:class:`.GroupInstance` is passed (or returned), the groups service is/should be
    available as the ``service`` property.
    """

    def get(self, name, service=None):
        """Get a group object representing the given group.

        :param    name: The name of the group.
        :type     name: str
        :param service: The service of the named group. If None, the group should not belong to any
            service.
        :type  service: :py:class:`~Services.models.Service` or None
        :return: A group object providing at least the properties of the GroupInstance class.
        :rtype: :py:class:`.GroupInstance`
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        """
        raise NotImplementedError

    def rm_user(self, group, user):
        """Remove a user from the group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param  user: A user as returned by :py:meth:`.UserBackend.get`.
        :type   user: :py:class:`.UserInstance`
        :raise: :py:class:`common.errors.UserNotFound` if the user is not a member of the group.
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

    def set_subgroups(self, group, subgroups):
        """Set all subgroups of a group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param subgroup: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  subgroup: :py:class:`.GroupInstance`
        """
        raise NotImplementedError


    def is_subgroup(self, group, subgroup):
        """Verify that a group is a subgroup of another group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param subgroup: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  subgroup: :py:class:`.GroupInstance`
        """
        raise NotImplementedError

    def subgroups(self, group, filter=True):
        """Get a list of subgroups.

        If ``filter=True``, the method should only return groups that belong to the same service as
        the given group. The returned list should be a list of strings, each representing a
        groupname.

        If ``filter=False``, the method should return all groups, regardless of their service. The
        list should contain :py:class:`.GroupInstance` objects.

        .. NOTE:: The filter argument is only False when called by some command line scripts.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param filter: Wether or not to filter for the groups service. See description for a
            detailled explanation.
        :type  filter: boolean
        :return: A list of subgroups.
        """
        raise NotImplementedError

    def has_subgroup(self, group, subgroup):
        """Test if a group is a subgroup of a different group.

        :param    group: The metagroup in question.
        :type     group: :py:class:`.GroupInstance`
        :param subgroup: The group that should be tested for a subgroup relationship.
        :type  subgroup: :py:class:`.GroupInstance`
        """
        raise NotImplementedError

    def rm_subgroup(self, group, subgroup):
        """Remove a subgroup from a group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
        :param subgroup: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  subgroup: :py:class:`.GroupInstance`
        :raise: :py:class:`common.errors.GroupNotFound` if the named subgroup is not actually a
            subgroup of group.
        """
        raise NotImplementedError

    def remove(self, group):
        """Remove a group.

        :param group: A group as provided by :py:meth:`.GroupBackend.get`.
        :type  group: :py:class:`.GroupInstance`
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
