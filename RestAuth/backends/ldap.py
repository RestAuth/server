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

from __future__ import absolute_import
from __future__ import unicode_literals

import ldap

from .base import BackendBase


class LDAPBackend(BackendBase):
    """
    :param LDAP_HOST: The ldap host to connect to, e.g. "ldap://localhost".
    :param LDAP_USER: The user used for binding, e.g. "cn=admin,dc=example,dc=com".
    :param LDAP_PASS: The password used for binding.
    :param USER_RDN: RDN for your user collection, e.g. "ou=people,dc=example,dc=com".
    :param GROUP_RDN: RDN for your group collection, e.g. "ou=people,dc=example,dc=com".
    :param USER_CLASSES: Object classes used for user objects. The first named object is assumed to be the
        primary object class.
    :param USER_ATTR: The attribute identifying a user.
    :param USER_SCOPE: Search scope used when searching for users, any of ldap.SCOPE_*. The default is
        ldap.SCOPE_BASE.
    :param GROUP_CLASSES: Object classes used for group objects. The first named object is assumed to be the
        primary object class.
    :param GROUP_ATTR: The attribute identifying a group.
    :param GROUP_SCOPE: Search scope used when searching for group, any of ldap.SCOPE_*. The default is
        ldap.SCOPE_BASE.
    """
    library = 'ldap'

    def __init__(self, LDAP_HOST, LDAP_USER, LDAP_PASS, USER_RDN, GROUP_RDN, USER_CLASSES=None,
                 USER_ATTR='uid', USER_SCOPE=None, GROUP_CLASSES=None, GROUP_ATTR='cn', GROUP_SCOPE=None):
        """
        Currently used for testing::

            LDAPBackend('ldap://localhost', 'cn=admin,dc=nodomain', 'nopass',
                        'ou=People,dc=nodomain', 'ou=Groups,dc=nodomain')
        """
        self.ldap = self._load_library()

        # set defaults for some kwargs
        if USER_CLASSES is None:
            USER_CLASSES = ['posixAccount', 'inetOrgPerson', 'shadowAccount']
        if GROUP_CLASSES is None:
            GROUP_CLASSES = ['posixGroup']
        if USER_SCOPE is None:
            USER_SCOPE = self.ldap.SCOPE_BASE
        if GROUP_SCOPE is None:
            GROUP_SCOPE = self.ldap.SCOPE_BASE

        # initiate connection
        self.conn = ldap.initialize(LDAP_HOST)
        self.conn.bind_s(LDAP_USER, LDAP_PASS, ldap.AUTH_SIMPLE)

        # set local attributes
        self.user_rdn = USER_RDN
        self.group_rdn = GROUP_RDN
        self.user_classes = [str(c) for c in USER_CLASSES]
        self.user_attr = USER_ATTR
        self.user_scope = USER_SCOPE
        self.group_classes = [str(c) for c in GROUP_CLASSES]
        self.group_attr = GROUP_ATTR
        self.group_scope = GROUP_SCOPE

        self.user_dn_tmpl = '%s=%%s,%s' % (USER_ATTR, USER_RDN)
        self.user_filter = '(objectclass=%s)' % USER_CLASSES[0]
        self.group_filter = '(object_class=%s)' % GROUP_CLASSES[0]
        self.group_dn_tmpl = '%s=%%s,%s' % (GROUP_ATTR, GROUP_RDN)

    TRANSACTION_MANAGER = None
    SUPPORTS_GROUP_VISIBILITY = False
    SUPPORTS_SUBGROUPS = False

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
        :param   password: The password to set. If not given, the user should not have a valid password and is
            unable to log in.
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
        cn = str('Firstname Lastname')
        sn = str('Lastname')
        if properties is not None:
            if 'full name' in properties:
                cn = properties['full name']
            elif 'first_name' in properties and 'last_name' in properties:
                cn = '%s %s' % (properties['first name'], properties['last name'])

        record = (
            ('objectclass', self.user_classes),
            (self.user_attr, user),
            ('cn', cn),
            ('uidNumber', str('123')),
            ('gidNumber', str('5000')),
            ('homeDirectory', str('/home/%s/' % user)),
            ('sn', sn),
        )
        try:
            return self.conn.add_s(self.user_dn_tmpl % user, record)
        except self.ldap.OBJECT_CLASS_VIOLATION:
            raise  # e.g. object does not have the right properties

    def list_users(self):
        """Get a list of all users.

        :return: A list of usernames.
        :rtype: list
        """
        results = self.conn.search_s(self.user_rdn, self.ldap.SCOPE_SUBTREE, self.user_filter,
                                     [str(self.user_attr)])
        return [v[self.user_attr][0] for k, v in results]

    def user_exists(self, user):
        """Determine if the user exists.

        :param user: The name of the user in question.
        :type  user: str
        :return: True if the user exists, False otherwise.
        :rtype: boolean
        """
        dn = '%s=%s,%s' % (self.user_attr, user, self.user_rdn)
        try:
            self.conn.search_s(dn, self.user_scope, str(self.user_filter), [str()])
            return True
        except ldap.NO_SUCH_OBJECT:
            return False

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
        :return: ``True`` if the password is correct and, if given, is a member in at least one of the given
            groups, ``False`` otherwise.
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
        :param depth: Override the recursion depth to use for meta-groups.  Normally, the backend should use
            :setting:`GROUP_RECURSION_DEPTH`.
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
        :raise: :py:class:`~common.errors.UserNotFound` if the named user does not exist or is not a member.
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
