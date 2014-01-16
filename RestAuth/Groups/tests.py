# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from django.utils import six
from django.utils.six.moves import http_client

from Services.models import Service
from Services.models import service_create
from common.compat import encode_str as _e
from common.testdata import CliMixin
from common.testdata import RestAuthTest
from common.testdata import capture
from common.testdata import group_backend
from common.testdata import groupname1
from common.testdata import groupname2
from common.testdata import groupname3
from common.testdata import groupname4
from common.testdata import groupname5
from common.testdata import groupname6
from common.testdata import password1
from common.testdata import password2
from common.testdata import password3
from common.testdata import password4
from common.testdata import password5
from common.testdata import property_backend
from common.testdata import user_backend
from common.testdata import username1
from common.testdata import username2
from common.testdata import username3
from common.testdata import username4
from common.testdata import username5

cli = getattr(__import__('bin.restauth-group'), 'restauth-group').main


class GroupTests(RestAuthTest):
    def setUp(self):
        RestAuthTest.setUp(self)

        # two users, so we can make sure nothing leaks to the other user
        self.user1 = self.create_user(username1, password1)
        self.user2 = self.create_user(username2, password2)
        self.user3 = self.create_user(username3, password3)

        self.vowi = Service.objects.get(username='vowi')
        self.fsinf = service_create('fsinf', 'fsinf', '127.0.0.1', '::1')

    def get_grp(self, name, service=None):
        return group_backend.get(service=service, name=name)


class GetGroupsTests(GroupTests):  # GET /groups/
    def test_get_no_groups(self):
        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_get_one_group(self):
        self.create_group(self.vowi, groupname1)

        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [groupname1])

    def test_get_two_groups(self):
        self.create_group(self.vowi, groupname1)
        self.create_group(self.vowi, groupname2)

        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1, groupname2])

    def test_service_isolation(self):
        self.create_group(self.vowi, groupname1)
        self.create_group(self.fsinf, groupname4)
        self.create_group(None, groupname5)

        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1])


class GetGroupsOfUserTests(GroupTests):  # GET /groups/?user=<user>
    def test_user_doesnt_exist(self):
        resp = self.get('/groups/', {'user': username5})

        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_no_memberships(self):
        # we add a group where user1 is NOT a member:
        self.create_group(self.vowi, groupname1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_one_membership(self):
        group1 = self.create_group(self.vowi, groupname1)
        group_backend.add_user(group1, self.user1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [groupname1])

        # test that user2 still has no memberships:
        resp = self.get('/groups/', {'user': username2})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_two_memberships(self):
        group1 = self.create_group(self.vowi, groupname1)
        group_backend.add_user(group1, self.user1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1])

        # test that user2 still has no memberships:
        resp = self.get('/groups/', {'user': username2})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_simple_inheritance(self):
        group1 = self.create_group(self.vowi, groupname1)
        group2 = self.create_group(self.vowi, groupname2)
        group_backend.add_user(group1, self.user1)
        group_backend.add_subgroup(group1, group2)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1, groupname2])

    def test_multilevel_inheritance(self):
        group1 = self.create_group(self.vowi, groupname1)
        group2 = self.create_group(self.vowi, groupname2)
        group3 = self.create_group(self.vowi, groupname3)
        group_backend.add_user(group1, self.user1)
        group_backend.add_subgroup(group1, group2)
        group_backend.add_subgroup(group2, group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1, groupname2, groupname3])

    def test_interservice_inheritance(self):
        group1 = self.create_group(None, groupname1)
        group2 = self.create_group(self.fsinf, groupname2)
        group3 = self.create_group(self.vowi, groupname3)
        group_backend.add_user(group1, self.user1)
        group_backend.add_subgroup(group1, group2)
        group_backend.add_subgroup(group2, group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname3])

    def test_distinct_inheritance(self):
        """
        This test checks if the call may return groups several times.
        This may occur if a user is member in several groups.
        """
        group1 = self.create_group(self.vowi, groupname1)
        group2 = self.create_group(self.vowi, groupname2)
        group3 = self.create_group(self.vowi, groupname3)

        group_backend.add_user(group1, self.user1)
        group_backend.add_user(group2, self.user1)
        group_backend.add_user(group3, self.user1)

        group_backend.add_subgroup(group1, group2)
        group_backend.add_subgroup(group2, group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1, groupname2, groupname3])

    def test_hidden_intermediate_dependencies(self):
        # membership to group2 is invisible, because it belongs to a different
        # service.
        group1 = self.create_group(self.vowi, groupname1)
        group2 = self.create_group(self.fsinf, groupname2)
        group3 = self.create_group(self.vowi, groupname3)
        group_backend.add_user(group1, self.user1)
        group_backend.add_subgroup(group1, group2)
        group_backend.add_subgroup(group2, group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1, groupname3])


class CreateGroupTests(GroupTests):  # POST /groups/
    def test_create_group(self):
        resp = self.post('/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertItemsEqual(group_backend.list(self.vowi), [groupname1])

    def test_create_existing_group(self):
        self.create_group(self.vowi, groupname1)

        resp = self.post('/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CONFLICT)
        self.assertItemsEqual(group_backend.list(self.vowi), [groupname1])

    def test_service_isolation(self):
        self.create_group(self.fsinf, groupname1)

        resp = self.post('/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertItemsEqual(group_backend.list(self.vowi), [groupname1])
        self.assertItemsEqual(group_backend.list(self.fsinf), [groupname1])

    def test_invalid_resource(self):
        resp = self.post('/groups/', {'group': 'foo/bar'})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertItemsEqual(group_backend.list(self.vowi), [])


class VerifyGroupExistanceTests(GroupTests):  # GET /groups/<group>/
    def test_does_not_exist(self):
        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_exists(self):
        self.create_group(self.vowi, groupname1)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

    def test_for_leaking_services(self):
        self.create_group(self.fsinf, groupname1)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_for_groups_with_no_service(self):
        self.create_group(None, groupname1)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')


class DeleteGroupTests(GroupTests):  # DELETE /groups/<group>/
    def test_does_not_exist(self):
        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_delete(self):
        self.create_group(self.vowi, groupname1)

        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertEqual(group_backend.list(self.vowi), [])

    def test_service_isolation(self):
        self.create_group(self.fsinf, groupname1)
        self.create_group(None, groupname2)

        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.delete('/groups/%s/' % groupname2)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(group_backend.list(self.vowi), [])
        self.assertItemsEqual(group_backend.list(self.fsinf), [groupname1])
        self.assertItemsEqual(group_backend.list(None), [groupname2])


class GroupUserTests(GroupTests):
    def setUp(self):
        GroupTests.setUp(self)

        self.group1 = self.create_group(self.vowi, groupname1)
        self.group2 = self.create_group(self.vowi, groupname2)
        self.group3 = self.create_group(self.vowi, groupname3)
        self.group4 = self.create_group(self.fsinf, groupname4)
        self.group5 = self.create_group(self.fsinf, groupname5)


class GetUsersInGroupTests(GroupUserTests):  # GET /groups/<group>/users/
    def test_group_does_not_exist(self):
        resp = self.get('/groups/%s/users/' % groupname6)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_service_isolation(self):
        resp = self.get('/groups/%s/users/' % groupname4)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.get('/groups/%s/users/' % groupname5)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_no_users(self):
        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_one_user(self):
        group_backend.add_user(self.group1, self.user1)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [username1])

    def test_two_users(self):
        group_backend.add_user(self.group1, self.user1)
        group_backend.add_user(self.group1, self.user2)
        group_backend.add_user(self.group2, self.user3)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])

    def test_simple_inheritance(self):
        group_backend.add_user(self.group1, self.user1)
        group_backend.add_user(self.group1, self.user2)
        group_backend.add_user(self.group2, self.user3)
        group_backend.add_subgroup(self.group1, self.group2)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])

        # group3 has users1-3, because of inheritance
        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2, username3])

    def test_multilevel_inheritance(self):
        group_backend.add_user(self.group1, self.user1)
        group_backend.add_user(self.group2, self.user2)
        group_backend.add_user(self.group3, self.user3)
        group_backend.add_subgroup(self.group1, self.group2)
        group_backend.add_subgroup(self.group2, self.group3)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1])

        # group2 has users1-2, because of inheritance
        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])

        # similar: gorup 3 has all users:
        resp = self.get('/groups/%s/users/' % groupname3)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2, username3])

    def test_hidden_inheritance(self):
        """
        Test a complex group-inheritance pattern.

        group 5, service=None, direct-members: user1, user2
        |- group 1, service=vowi, direct-members: user3
           |- group 4, service=fsinf, direct-members: user4
              |- group 2, service=vowi, direct-members: user5
        """
        # set up data structure:
        self.user4 = self.create_user(username4, password4)
        self.user5 = self.create_user(username5, password5)

        # group 5 has no service (hidden "global" group)
        group_backend.add_user(self.group5, self.user1)
        group_backend.add_user(self.group5, self.user2)
        group_backend.add_subgroup(self.group5, self.group1)
        group_backend.add_user(self.group1, self.user3)
        group_backend.add_subgroup(self.group1, self.group4)  # group4 is fsinf service
        group_backend.add_user(self.group4, self.user4)
        group_backend.add_subgroup(self.group4, self.group2)
        group_backend.add_user(self.group2, self.user5)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2, username3])

        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertItemsEqual(self.parse(resp, 'list'),
                              [username1, username2, username3, username4, username5])


class AddUserToGroupTests(GroupUserTests):  # POST /groups/<group>/users/
    def test_group_doesnt_exist(self):
        resp = self.post('/groups/%s/users/' % groupname6, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_user_doesnt_exist(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username5})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_user_and_group_dont_exist(self):
        resp = self.post('/groups/%s/users/' % groupname6, {'user': username5})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_add_user(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.members(self.group1), [self.user1.username])
        self.assertItemsEqual(group_backend.members(self.group2), [])
        self.assertItemsEqual(group_backend.members(self.group3), [])

    def test_add_user_twice(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.members(self.group1), [self.user1.username])
        self.assertItemsEqual(group_backend.members(self.group2), [])
        self.assertItemsEqual(group_backend.members(self.group3), [])

        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.members(self.group1), [self.user1.username])
        self.assertItemsEqual(group_backend.members(self.group2), [])
        self.assertItemsEqual(group_backend.members(self.group3), [])

    def test_service_isolation(self):
        resp = self.post('/groups/%s/users/' % groupname4, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(group_backend.members(self.get_grp(groupname4, self.fsinf)), [])

        resp = self.post('/groups/%s/users/' % groupname5, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(group_backend.members(self.get_grp(groupname5, self.fsinf)), [])

    def test_bad_requests(self):
        resp = self.post('/groups/%s/users/' % groupname1, {})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)

        resp = self.post('/groups/%s/users/' % groupname1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)

        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1, 'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)


# GET /groups/<group>/users/<user>/
class VerifyUserInGroupTests(GroupUserTests):
    def is_member(self, groupname, username):
        """
        Test if user is a member. Throws assertion error if the group doesn't
        exist.
        """
        resp = self.get('/groups/%s/users/%s/' % (groupname, username))
        if resp.status_code == http_client.NO_CONTENT:
            return True
        else:
            self.assertEqual(resp.status_code, http_client.NOT_FOUND)
            self.assertEqual(resp['Resource-Type'], 'user')
            return False

    def test_group_doesnt_exist(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname6, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_group_and_user_dont_exist(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname6, username4))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_service_isolation(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        group_backend.add_user(self.group4, self.user1)

        resp = self.get('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_user_doesnt_exist(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname1, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_user_not_in_group(self):
        self.assertFalse(self.is_member(groupname1, username1))
        self.assertFalse(self.is_member(groupname2, username1))

    def test_user_in_group(self):
        group_backend.add_user(self.group1, self.user1)

        self.assertTrue(self.is_member(groupname1, username1))
        self.assertFalse(self.is_member(groupname2, username1))

    def test_simple_inheritance(self):
        group_backend.add_user(self.group1, self.user1)
        group_backend.add_user(self.group2, self.user2)
        group_backend.add_subgroup(self.group1, self.group2)

        # user1 is member in group1 and group2:
        self.assertTrue(self.is_member(groupname1, username1))
        self.assertTrue(self.is_member(groupname2, username1))

        # user2 is member in group2, not in group1
        self.assertFalse(self.is_member(groupname1, username2))
        self.assertTrue(self.is_member(groupname2, username2))

    def test_multilevel_inheritance(self):
        """
        Test a complex group-inheritance pattern.

        group 5, service=None, direct-members: user1, user2
        |- group 1, service=vowi, direct-members: user3
           |- group 4, service=fsinf, direct-members: user4
              |- group 2, service=vowi, direct-members: user5
        """
        # set up data structure:
        self.user4 = self.create_user(username4, password4)
        self.user5 = self.create_user(username5, password5)

        # group 5 has no service (hidden "global" group)
        group_backend.add_user(self.group5, self.user1)
        group_backend.add_user(self.group5, self.user2)
        group_backend.add_subgroup(self.group5, self.group1)
        group_backend.add_user(self.group1, self.user3)
        group_backend.add_subgroup(self.group1, self.group4)  # group4 is fsinf service
        group_backend.add_user(self.group4, self.user4)
        group_backend.add_subgroup(self.group4, self.group2)
        group_backend.add_user(self.group2, self.user5)

        # user1 and user2 are member in group5 and thus also in group1 and
        # group2
        self.assertTrue(self.is_member(groupname1, username1))
        self.assertTrue(self.is_member(groupname1, username2))
        self.assertTrue(self.is_member(groupname2, username1))
        self.assertTrue(self.is_member(groupname2, username2))

        # user3 is member in group1, thus also in group2:
        self.assertTrue(self.is_member(groupname1, username3))
        self.assertTrue(self.is_member(groupname2, username3))

        # user4 is member in group4, thus also in group2:
        self.assertFalse(self.is_member(groupname1, username4))
        self.assertTrue(self.is_member(groupname2, username4))

        # user5 is member only group2:
        self.assertFalse(self.is_member(groupname1, username5))
        self.assertTrue(self.is_member(groupname2, username5))


# DELETE /groups/<group>/users/<user>/
class DeleteUserFromGroupTests(GroupUserTests):
    def test_group_doesnt_exist(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname6, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_user_doesnt_exist(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname1, username5))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_user_and_group_dont_exist(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname6, username5))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_delete_user(self):
        group_backend.add_user(self.group1, self.user1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname1, username1))
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

    def test_user_not_member(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname1, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_service_isolation(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(group_backend.members(self.group4), [])

        group_backend.add_user(self.group4, self.user1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(group_backend.members(self.group4), [self.user1.username])

        # same as above except for global group:
        resp = self.delete('/groups/%s/users/%s/' % (groupname5, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(group_backend.members(self.group5), [])

        group_backend.add_user(self.group5, self.user1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname5, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(group_backend.members(self.group5), [self.user1.username])


class GetSubGroupTests(GroupUserTests):  # GET /groups/<group>/groups/
    def test_group_doesnt_exist(self):
        resp = self.get('/groups/%s/groups/' % groupname6)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_get_no_subgroups(self):
        group_backend.add_subgroup(self.group2, self.group4)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertEqual(self.parse(resp, 'list'), [])

    def test_get_one_subgroup(self):
        group_backend.add_subgroup(self.group1, self.group2)
        group_backend.add_subgroup(self.group1, self.group5)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertEqual(self.parse(resp, 'list'), [groupname2])

    def test_get_two_subgroups(self):
        group_backend.add_subgroup(self.group1, self.group2)
        group_backend.add_subgroup(self.group1, self.group3)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertItemsEqual(self.parse(resp, 'list'), [groupname2, groupname3])

    def test_service_isolation(self):
        group_backend.add_subgroup(self.group1, self.group2)
        group_backend.add_subgroup(self.group1, self.group4)
        group_backend.add_subgroup(self.group1, self.group5)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertEqual(self.parse(resp, 'list'), [groupname2])


class AddSubGroupTests(GroupUserTests):  # POST /groups/<group>/groups/
    def test_group_doesnt_exist(self):
        resp = self.post('/groups/%s/groups/' % groupname6, {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(group_backend.exists(name=groupname6, service=self.vowi))
        subgroups = group_backend.subgroups(group=self.group1, filter=True)
        self.assertEqual(subgroups, [])

    def test_subgroup_doesnt_exist(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname6})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(group_backend.exists(name=groupname6, service=self.vowi))
        self.assertItemsEqual(group_backend.subgroups(self.get_grp(groupname1, self.vowi)), [])

    def test_add_subgroup(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [self.group2])
        self.assertItemsEqual(group_backend.parents(
            self.get_grp(groupname2, self.vowi)), [self.group1])

    def test_add_subgroup_twice(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [self.group2])
        self.assertItemsEqual(group_backend.parents(self.group2), [self.group1])

        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [self.group2])
        self.assertItemsEqual(group_backend.parents(self.group2), [self.group1])

    def test_bad_requests(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])

        resp = self.post('/groups/%s/groups/' % groupname1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])

        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2, 'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])

    def test_service_isolation(self):
        # we shouldn't be able to add a subgroup:
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname4})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])
        self.assertItemsEqual(group_backend.parents(self.get_grp(groupname4, self.fsinf)), [])

        # same with global group:
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname5})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])
        self.assertItemsEqual(group_backend.parents(self.get_grp(groupname5, self.fsinf)), [])


# DELETE /groups/<group>/groups/<subgroup>/
class RemoveSubGroupTests(GroupUserTests):
    def test_group_doesnt_exist(self):
        resp = self.delete('/groups/%s/groups/%s/' % (groupname6, groupname1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(group_backend.exists(name=groupname6, service=self.vowi))
        self.assertItemsEqual(group_backend.subgroups(
            group=self.get_grp(groupname1, self.vowi), filter=False), [])

    def test_subgroup_doesnt_exist(self):
        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname6))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(group_backend.exists(name=groupname6, service=self.vowi))
        self.assertItemsEqual(group_backend.subgroups(
            group=self.get_grp(groupname1, self.vowi), filter=False), [])

    def test_remove_subgroup(self):
        group_backend.add_subgroup(self.group1, self.group2)
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [self.group2])
        self.assertItemsEqual(
            group_backend.parents(self.get_grp(groupname2, self.vowi)), [self.group1])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])
        self.assertItemsEqual(group_backend.parents(self.get_grp(groupname2, self.vowi)), [])

    def test_remove_invalid_subgroup(self):
        # try to remove subgroup thats not really a subgroup
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname2, self.vowi), filter=False), [])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname1, self.vowi), filter=False), [])
        self.assertItemsEqual(group_backend.subgroups(
            self.get_grp(groupname2, self.vowi), filter=False), [])

    def test_service_isolation(self):
        group_backend.add_subgroup(self.group1, self.group4)
        group_backend.add_subgroup(self.group1, self.group5)
        group1 = self.get_grp(groupname1, self.vowi)
        self.assertItemsEqual(group_backend.subgroups(group1, filter=False),
                              [self.group4, self.group5])
        self.assertItemsEqual(group_backend.parents(self.get_grp(groupname4, self.fsinf)),
                              [self.group1])
        self.assertItemsEqual(group_backend.parents(
            self.get_grp(groupname5, self.fsinf)), [self.group1])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname4))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname5))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        # nothing has changed!?
        group1 = self.get_grp(groupname1, self.vowi)
        self.assertItemsEqual(group_backend.subgroups(group1, filter=False),
                              [self.group4, self.group5])
        self.assertItemsEqual(group_backend.parents(self.get_grp(groupname4, self.fsinf)),
                              [self.group1])
        self.assertItemsEqual(group_backend.parents(self.get_grp(groupname5, self.fsinf)),
                              [self.group1])


class CliTests(RestAuthTest, CliMixin):
    def test_add(self):
        with capture() as (stdout, stderr):
            cli(['add', groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(group_backend.exists(groupname1))

        with capture() as (stdout, stderr):
            cli(['add', '--service=%s' % self.service.username, groupname2 if six.PY3 else
                 groupname2.encode('utf-8')])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(group_backend.exists(groupname2, service=self.service))

    def test_add_exists(self):
        group_backend.create(groupname1)
        group_backend.create(groupname2, service=self.service)

        with capture() as (stdout, stderr):
            try:
                cli(['add', groupname1 if six.PY3 else groupname1.encode('utf-8')])
                self.fail('Adding an already existing group does not throw an error.')
            except SystemExit as e:
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'Group already exists\.')

        with capture() as (stdout, stderr):
            try:
                cli(['add', '--service=%s' % self.service.username, groupname2 if six.PY3 else
                     groupname2.encode('utf-8')])
                self.fail('Adding an already existing group does not throw an error.')
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'Group already exists\.')

    def test_ls(self):
        group_backend.create(groupname1)
        group_backend.create(groupname2)
        group_backend.create(groupname3, service=self.service)
        group_backend.create(groupname4, service=self.service)

        with capture() as (stdout, stderr):
            cli(['ls'])
            self.assertEqual(stdout.getvalue(), '%s\n%s\n' % (groupname1, groupname2))
            self.assertEqual(stderr.getvalue(), '')

        with capture() as (stdout, stderr):
            cli(['ls', '--service=%s' % self.service.username])
            self.assertEqual(stdout.getvalue(), '%s\n%s\n' % (groupname3, groupname4))
            self.assertEqual(stderr.getvalue(), '')

    def test_view(self):
        user1 = user_backend.create(username1, property_backend=property_backend)
        user2 = user_backend.create(username2, property_backend=property_backend)
        user3 = user_backend.create(username3, property_backend=property_backend)
        group1 = group_backend.create(groupname1)
        group2 = group_backend.create(groupname2)
        group3 = group_backend.create(groupname3)
        group4 = group_backend.create(groupname4, service=self.service)
        group5 = group_backend.create(groupname5, service=self.service)

        with capture() as (stdout, stderr):
            cli(['view', groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stderr.getvalue(), '')
            self.assertEqual(stdout.getvalue(), """* No explicit members
* No effective members
* No parent groups
* No subgroups
""")

        # add a few members, and subgroups:
        group_backend.add_user(group1, user1)
        group_backend.add_user(group1, user2)
        group_backend.add_user(group4, user3)
        group_backend.add_subgroup(group1, group2)
        group_backend.add_subgroup(group1, group4)
        group_backend.add_subgroup(group5, group4)

        # view a top-group:
        with capture() as (stdout, stderr):
            cli(['view', groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stderr.getvalue(), '')
            userlist = ', '.join(sorted([username1, username2]))
            self.assertEqual(stdout.getvalue(), """* Explicit members: %s
* Effective members: %s
* No parent groups
* Subgroups:
    <no service>: %s
    %s: %s
""" % (userlist, userlist, groupname2, self.service.name, groupname4))

        # view a sub-group
        with capture() as (stdout, stderr):
            cli(['view', '--service=%s' % self.service.username,
                 groupname4 if six.PY3 else groupname4.encode('utf-8')])
            self.assertEqual(stderr.getvalue(), '')
            explicit = ', '.join(sorted([username3, ]))
            effective = ', '.join(sorted([username1, username2, username3]))
            self.assertEqual(stdout.getvalue(), """* Explicit members: %s
* Effective members: %s
* Parent groups:
    <no service>: %s
    %s: %s
* No subgroups
""" % (explicit, effective, groupname1, self.service.username, groupname5))

    def test_set_service(self):
        group_backend.create(groupname1)

        with capture() as (stdout, stderr):
            cli(['set-service', groupname1 if six.PY3 else groupname1.encode('utf-8'),
                 self.service.username])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.list(service=self.service), [groupname1])

        with capture() as (stdout, stderr):
            cli(['set-service', '--service=%s' % self.service.username,
                 groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.list(service=None), [groupname1])

        with capture() as (stdout, stderr):  # test a non-existing group
            try:
                cli(['set-service', '--service=%s' % self.service.username,
                     groupname1 if six.PY3 else groupname1.encode('utf-8')])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: %s at service %s: Group does not exist\.$' %
                                   (groupname1, self.service.username))
        self.assertEqual(group_backend.list(service=None), [groupname1])

    def test_add_user(self):
        user1 = user_backend.create(username1, property_backend=property_backend)
        user2 = user_backend.create(username2, property_backend=property_backend)
        group1 = group_backend.create(groupname1)
        group2 = group_backend.create(groupname2, service=self.service)

        with capture() as (stdout, stderr):
            cli(['add-user',
                 groupname1 if six.PY3 else groupname1.encode('utf-8'),
                 username1 if six.PY3 else username1.encode('utf-8'),
            ])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.members(group1), [username1])

        with capture() as (stdout, stderr):
            cli(['add-user', '--service=%s' % self.service.username,
                 groupname2 if six.PY3 else groupname2.encode('utf-8'),
                 username2 if six.PY3 else username2.encode('utf-8'),
            ])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.members(group2), [username2])

    def test_add_group_neither(self):  # neither group is in any service
        group1 = group_backend.create(groupname1)
        group2 = group_backend.create(groupname2)

        with capture() as (stdout, stderr):
            cli(['add-group',
                 groupname1 if six.PY3 else groupname1.encode('utf-8'),
                 groupname2 if six.PY3 else groupname2.encode('utf-8'),
            ])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.subgroups(group1), [groupname2])

    def test_add_group_both(self):  # bout groups are in service
        group1 = group_backend.create(groupname1, service=self.service)
        group2 = group_backend.create(groupname2, service=self.service)

        with capture() as (stdout, stderr):
            cli(['add-group', '--service=%s' % self.service.username,
                 '--sub-service=%s' % self.service.username, _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.subgroups(group1), [groupname2])

    def test_rename(self):
        group_backend.create(groupname1)
        group_backend.create(groupname3)
        group_backend.create(groupname1, service=self.service)

        with capture() as (stdout, stderr):
            cli(['rename', _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.list(service=None), [groupname2, groupname3])

        with capture() as (stdout, stderr):
            cli(['rename', '--service=%s' % self.service.username, _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.list(service=self.service), [groupname2])

        # test a failed rename
        with capture() as (stdout, stderr):
            try:
                cli(['rename', _e(groupname3), _e(groupname2)])  # groupname2 already exists
                self.fail("Rename doesn't fail")
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: %s: Group already exists\.$' % groupname2)
        self.assertEqual(group_backend.list(service=None), [groupname2, groupname3])

    def test_rm(self):
        group_backend.create(groupname1)
        with capture() as (stdout, stderr):
            cli(['rm', _e(groupname1)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.list(service=None), [])

    def test_rm_user(self):
        group = group_backend.create(groupname1)
        user = user_backend.create(username1, property_backend=property_backend)
        group_backend.add_user(group, user)
        self.assertEqual(group_backend.members(group), [username1])

        with capture() as (stdout, stderr):
            cli(['rm-user', _e(groupname1), _e(username1)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.members(group), [])

        with capture() as (stdout, stderr):
            try:
                cli(['rm-user', _e(groupname1), _e(username1)])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    'error: User "%s" not member of group "%s"\.$' % (username1, groupname1))
        self.assertEqual(group_backend.members(group), [])

    def test_rm_group(self):
        group1 = group_backend.create(groupname1)
        group2 = group_backend.create(groupname2)
        group_backend.add_subgroup(group1, group2)
        self.assertEqual(group_backend.subgroups(group1), [groupname2])

        with capture() as (stdout, stderr):
            cli(['rm-group', _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(group_backend.subgroups(group1), [])

        with capture() as (stdout, stderr):
            try:
                cli(['rm-group', _e(groupname1), _e(groupname2)])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    'error: Group "%s" is not a subgroup of "%s"\.$' % (groupname2, groupname1))
        self.assertEqual(group_backend.subgroups(group1), [])
