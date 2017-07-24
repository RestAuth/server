# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not, see
# <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, absolute_import

import importlib


class TransactionManagerBase(object):
    def __init__(self, backend, dry=False):
        self.backend = backend
        self.dry = dry

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError


class BackendBase(object):  # pragma: no cover
    _library = None
    library = None

    TRANSACTION_MANAGER = None
    SUPPORTS_GROUP_VISIBILITY = True
    SUPPORTS_SUBGROUPS = True

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

        This method is exclusively used in unit tests. It should perform any actions necessary to start a unit
        test. In general, this should test that there are currently no users or groups present.
        """
        pass

    def testTearDown(self):
        """Tear down your backend after a test run.

        This method is exclusively used in unit tests. It should perform any actions necessary after a unit
        test. In general, this should completely remove all users, their properties and all groups created
        during a unit test.
        """
        pass

    def transaction(self, dry=False):
        return self.TRANSACTION_MANAGER(backend=self, dry=dry)

    def create_user(self, user, password=None, properties=None, groups=None, dry=False):
        """Create a new user.

        The ``user`` is already validated, so you don't need to do any additional validation here. If your
        backend has username restrictions, please implement a :ref:`username validator
        <implement-validators>`.

        The ``dry`` parameter tells you if you should actually create the user. The parameter will be True for
        `dry-runs <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a dry-run, the method should
        behave as closely as possible to a normal invocation but shouldn't actually create the user.

        The ``groups`` parameter is a list of tuples with the first element being the name of the group and
        the second element being the service of that group. Groups that do not exist should be automatically
        created.

        Example::

            create_user('username', 'password', {'email': 'user@example.com'},
                        groups=[('subgroup1', <Service: example.com>),
                                ('subgroup2', <Service: example.net>)]
            )

        :param   user: The username.
        :type    user: str
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
        :raise: :py:class:`~common.errors.UserExists` if the user already exist.
        """
        raise NotImplementedError

    def list_users(self):
        """Get a list of all users.

        :return: A list of usernames.
        :rtype: list
        """
        raise NotImplementedError

    def user_exists(self, user):
        """Determine if the user exists.

        :param user: The name of the user in question.
        :type  user: str
        :return: True if the user exists, False otherwise.
        :rtype: boolean
        """
        raise NotImplementedError

    def rename_user(self, user, name):
        """Rename a user.

        This operation is only used by |bin-restauth-user-doc|.

        :param user: The name of the user to rename.
        :type  user: str
        :param     name: The new username.
        :type      name: str
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        :raise: :py:class:`~common.errors.UserExists` if a user with the new name already exist.
        """
        raise NotImplementedError

    def check_password(self, user, password, groups=None):
        """Check a users password.

        If the ``groups`` parameter is given, the backend should also check if the user is a member in at
        least one of the given groups.

        :param user: The username.
        :type  user: str
        :param password: The password to check.
        :type  password: str
        :param groups: A list of groups, the format is the same as in :py:func:`create_user`.
        :type  groups: list
        :return: ``True`` if the password is correct and, if given, is a member in at least one of
            the given groups, ``False`` otherwise.
        :rtype: boolean
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_password(self, user, password=None):
        """Set a new password.

        :param user: The username.
        :type  user: str
        :param password: The new password. If None or empty, the user should get an unusable password.
        :type  password: str
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_password_hash(self, user, algorithm, hash):
        """Set a users password hash.

        This method is called by |bin-restauth-import| if users with a password hash should be imported.

        If you can store password hashes as an arbitrary string and then use Djangos password hashing
        framework for verifying those hashes, you can import the hash like this::

            from common.hashers import import_hash
            django_hash = import_hash(algorithm, hash)

        :param user: The username.
        :type  user: str
        :param algorithm: The algorithm used for creating the hash.
        :type  algorithm: str
        :param      hash: The hash created by the algorithm.
        :type       hash: str
        """
        raise NotImplementedError

    def remove_user(self, user):
        """Remove a user.

        :param user: The username.
        :type  user: str
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def get_properties(self, user):
        """Get a full list of all user properties.

        :param user: The username.
        :type  user: str
        :return: A dictionary of key/value pairs, each describing a property.
        :rtype: dict
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def create_property(self, user, key, value, dry=False):
        """Create a new user property.

        This method should return :py:class:`~common.errors.PropertyExists` if a property with the given key
        already exists.

        The ``dry`` parameter tells you if you should actually create the property. The parameter will be True
        for `dry-runs <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a dry-run, the method
        should behave as closely as possible to a normal invocation but shouldn't actually create the
        property.

        :param user: The username.
        :type  user: str
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

    def get_property(self, user, key):
        """Get a specific property of the user.

        :param user: The username.
        :type  user: str
        :param key: The key identifying the property.
        :type  key: str
        :return: The value of the property.
        :rtype: str
        :raise: :py:class:`common.errors.PropertyNotFound` if the property doesn't exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_property(self, user, key, value):
        """Set a property for the given user.

        Unlike :py:meth:`~.PropertyBackend.create` this method overwrites an existing property.

        :param user: The username.
        :type  user: str
        :param key: The key identifying the property.
        :type  key: str
        :param value: The value of the property.
        :type  value: str
        :return: ``None`` if the property didn't exist previously or the old value, if it did.
        :rtype: str or None
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def set_properties(self, user, properties):
        """Set multiple properties at once.

        This method may just call :py:meth:`~.PropertyBackend.set` multiple times. Some backends have faster
        methods for setting multiple values at once, though.

        :param user: The username.
        :type  user: str
        :param properties: A dictionary of properties.
        :type  properties: dict
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def remove_property(self, user, key):
        """Remove a property.

        :param user: The username.
        :type  user: str
        :param key: The key identifying the property.
        :type  key: str
        :raise: :py:class:`common.errors.PropertyNotFound` if the property doesn't exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def list_groups(self, service, user=None):
        """Get a list of group names for the given service.

        :param service: The service of the named group.
        :param user: If given, only return groups that the user is a member of.
        :type  user: str
        :return: list of strings, each representing a group name.
        :rtype: list
        :raise: :py:class:`~common.errors.UserNotFound` if the user doesn't exist.
        """
        raise NotImplementedError

    def create_group(self, group, service, users=None, dry=False):
        """Create a new group for the given service.

        The ``dry`` parameter tells you if you should actually create the group. The parameter will be True
        for `dry-runs <https://restauth.net/wiki/Specification#Doing_dry-runs>`_. In a dry-run, the method
        should behave as closely as possible to a normal invocation but shouldn't actually create the group.

        :param group: The name of the group.
        :type  group: str
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

    def rename_group(self, group, name, service):
        """Rename a group.

        This operation is only available via |bin-restauth-group-doc|.

        :param group: The old name of the group.
        :type  group: str
        :param name: The new name of the group.
        :type  name: str
        :param service: The service of the group.
        :type  service: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`~common.errors.GroupNotFound` if the old group does not exist.
        :raise: :py:class:`~common.errors.GroupExists` if the group already exist.
        """
        raise NotImplementedError

    def set_service(self, group, service, new_service):
        """Set the service of a group.

        This operation is only available via |bin-restauth-group-doc|.

        :param group: The name of the group.
        :type  group: str
        :param service: The old service of the group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param new_service: The new service of the group.
        :type  new_service: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`~common.errors.GroupNotFound` if the old group does not exist.
        :raise: :py:class:`~common.errors.GroupExists` if the new group already exist.
        """
        raise NotImplementedError

    def group_exists(self, group, service):
        """Determine if a group exists for the given service.

        :param   group: The name of the group.
        :type    group: str
        :param service: The service of the group to query.
        :type  service: :py:class:`~Services.models.Service` or None
        :return: True if the group exists, False otherwise.
        :rtype: boolean
        """
        raise NotImplementedError

    def set_memberships(self, user, service, groups):
        """Set groups for a user.

        :param user: The name of the user.
        :type  user: str
        :param service: The service of all groups to add to.
        :type  service: :py:class:`~Services.models.Service` or None
        :param groups: A list of groupnames. Groups that don't exist have to be created.
        :type  groups: list of str
        :raise: :py:class:`~common.errors.UserNotFound` if the user does not exist.
        """
        raise NotImplementedError

    def set_members(self, group, service, users):
        """Set all members of a group.

        This method replaces the current list of members with the one passed by ``users``. If a user is member
        of a meta-group, this method must not remove that membership if the user is not in the new list of
        members.

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

    def add_member(self, group, service, user):
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

    def remove_member(self, group, service, user):
        """Remove a user from the group.

        :param group: A group from which to remove the user.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param  user: The user to remove.
        :type   user: str
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        :raise: :py:class:`~common.errors.UserNotFound` if the named user does not exist or is not
            a member.
        """
        raise NotImplementedError

    def add_subgroup(self, group, service, subgroup, subservice):
        """Make a group a subgroup of another group.

        :param group: The future parent group.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param subgroup: The future subgroup.
        :type  subgroup: str
        :param subservice: The service of the given group.
        :type  subservice: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        """
        raise NotImplementedError

    def set_subgroups(self, group, service, subgroups, subservice):
        """Set all subgroups of a group.

        :param group: The future parent group.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param subgroup: The future subgroup.
        :type  subgroup: str
        :param subservice: The service of the given group.
        :type  subservice: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        """
        raise NotImplementedError

    def is_subgroup(self, group, service, subgroup, subservice):
        """Verify that a group is a subgroup of another group.

        :param group: The parent group to test for.
        :type  group: str
        :param service: The service of the given group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param subgroup: The subgroup to testfor.
        :type  subgroup: str
        :param subservice: The service of the given group.
        :type  subservice: :py:class:`~Services.models.Service` or None
        :return: Wether the second given group is a subgroup of the first.
        :rtype: bool
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        """
        raise NotImplementedError

    def remove_subgroup(self, group, service, subgroup, subservice):
        """Remove a sub-group from a meta-group.

        :param group: The name of the meta-group.
        :type  group: str
        :param service: The service of the meta-group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param subgroup: The name of the sub-group.
        :type  subgroup: str
        :param subservice: The service of the sub-group.
        :type  subservice: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`common.errors.GroupNotFound` if the meta-group or subgroup are not
            found.
        """
        raise NotImplementedError

    def subgroups(self, group, service, filter=True):
        """Get a list of subgroups.

        If ``filter=True``, the method should only return groups that belong to the same service as the given
        group. The returned list should be a list of strings, each representing a groupname.

        If ``filter=False``, the method should return all groups, regardless of their service. The returned
        list should contain tuples with the name and service of the group.

        Example::

            >>> service = Service.objects.get(username='example.com')
            >>> backend.subgroups("groupname", service=service, filter=True)
            ['subgroup1']
            >>> backend.subgroups("groupname", service=service, filter=False)
            [('subgroup1', <Service: example.com>), ('subgroup2', <Service: example.net>)]

        .. NOTE:: The filter argument is only False when called by some command line scripts and in unittests.

        :param group: The name of the meta-group.
        :type  group: str
        :param service: The service of the meta-group.
        :type  service: :py:class:`~Services.models.Service` or None
        :param filter: Wether or not to filter for the groups service. See description for a
            detailled explanation.
        :type  filter: boolean
        :return: A list of sub-groups (see above).
        :raise: :py:class:`common.errors.GroupNotFound` if the meta-group is not found.
            found.
        """
        raise NotImplementedError

    def parents(self, group, service):
        """Get a list of all parent groups of a group.

        This method is only used by some command-line scripts, hence there is no need for a
        parameter limiting the returned groups to groups of the same service.

        :param group: The name of the sub-group.
        :type  group: str
        :param service: The service of the sub-group.
        :type  service: :py:class:`~Services.models.Service` or None
        :return: List of parent groups, each as tuple of name/service.
        :rtype: list
        """
        raise NotImplementedError

    def remove_group(self, group, service):
        """Remove a group.

        :param group: The name of the group to remove..
        :type  group: str
        :param service: The service of the group.
        :type  service: :py:class:`~Services.models.Service` or None
        :raise: :py:class:`common.errors.GroupNotFound` if the named group does not exist.
        """
        raise NotImplementedError
