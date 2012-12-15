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

import httplib

from RestAuth.Services.models import Service, service_create
from RestAuth.common.testdata import *
from RestAuth.Users.models import ServiceUser
from Groups import views
from Groups.models import *


class GroupTests(RestAuthTest):
    def setUp(self):
        RestAuthTest.setUp(self)

        # two users, so we can make sure nothing leaks to the other user
        self.user1 = user_create(username1, password1)
        self.user2 = user_create(username2, password2)
        self.user3 = user_create(username3, password3)

        self.vowi = Service.objects.get(username='vowi')
        self.fsinf = service_create('fsinf', 'fsinf', '127.0.0.1', '::1')

    def get_grp(self, name, service=None):
        return Group.objects.get(name=name, service=service)


class GetGroupsTests(GroupTests):  # GET /groups/
    def test_get_no_groups(self):
        resp = self.get('/groups/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [])

    def test_get_one_group(self):
        group_create(groupname1, self.vowi)

        resp = self.get('/groups/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [groupname1])

    def test_get_two_groups(self):
        group_create(groupname1, self.vowi)
        group_create(groupname2, self.vowi)

        resp = self.get('/groups/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [groupname1, groupname2])

    def test_service_isolation(self):
        group_create(groupname1, self.vowi)
        group_create(groupname4, self.fsinf)
        group_create(groupname5, None)

        resp = self.get('/groups/')
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1])


class GetGroupsOfUserTests(GroupTests):  # GET /groups/?user=<user>
    def test_user_doesnt_exist(self):
        resp = self.get('/groups/', {'user': username5})

        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_no_memberships(self):
        # we add a group where user1 is NOT a member:
        group1 = group_create(groupname1, self.vowi)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [])

    def test_one_membership(self):
        group1 = group_create(groupname1, self.vowi)
        group1.users.add(self.user1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [groupname1])

        # test that user2 still has no memberships:
        resp = self.get('/groups/', {'user': username2})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [])

    def test_two_memberships(self):
        group1 = group_create(groupname1, self.vowi)
        group1.users.add(self.user1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname1])

        # test that user2 still has no memberships:
        resp = self.get('/groups/', {'user': username2})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [])

    def test_simple_inheritance(self):
        group1 = group_create(groupname1, self.vowi)
        group2 = group_create(groupname2, self.vowi)
        group1.users.add(self.user1)
        group1.groups.add(group2)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [groupname1, groupname2])

    def test_multilevel_inheritance(self):
        group1 = group_create(groupname1, self.vowi)
        group2 = group_create(groupname2, self.vowi)
        group3 = group_create(groupname3, self.vowi)
        group1.users.add(self.user1)
        group1.groups.add(group2)
        group2.groups.add(group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [groupname1, groupname2, groupname3])

    def test_interservice_inheritance(self):
        group1 = group_create(groupname1, None)
        group2 = group_create(groupname2, self.fsinf)
        group3 = group_create(groupname3, self.vowi)
        group1.users.add(self.user1)
        group1.groups.add(group2)
        group2.groups.add(group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [groupname3])

    def test_distinct_inheritance(self):
        """
        This test checks if the call may return groups several times.
        This may occur if a user is member in several groups.
        """
        group1 = group_create(groupname1, self.vowi)
        group2 = group_create(groupname2, self.vowi)
        group3 = group_create(groupname3, self.vowi)

        group1.users.add(self.user1)
        group2.users.add(self.user1)
        group3.users.add(self.user1)

        group1.groups.add(group2)
        group2.groups.add(group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        actual = self.parse(resp, 'list')
        self.assertItemsEqual(self.parse(resp, 'list'),
                              [groupname1, groupname2, groupname3])

    def test_hidden_intermediate_dependencies(self):
        # membership to group2 is invisible, because it belongs to a different
        # service.
        group1 = group_create(groupname1, self.vowi)
        group2 = group_create(groupname2, self.fsinf)
        group3 = group_create(groupname3, self.vowi)
        group1.users.add(self.user1)
        group1.groups.add(group2)
        group2.groups.add(group3)

        resp = self.get('/groups/', {'user': username1})
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [groupname1, groupname3])


class VerifyGroupExistanceTests(GroupTests):  # GET /groups/<group>/
    def test_does_not_exist(self):
        resp = self.get('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_exists(self):
        group_create(groupname1, self.vowi)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

    def test_for_leaking_services(self):
        group_create(groupname1, self.fsinf)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_for_groups_with_no_service(self):
        group_create(groupname1, None)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')


class DeleteGroupTests(GroupTests):  # DELETE /groups/<group>/
    def test_does_not_exist(self):
        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_delete(self):
        group_create(groupname1, self.vowi)

        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertEquals(Group.objects.all().count(), 0)

    def test_service_isolation(self):
        group1 = group_create(groupname1, self.fsinf)
        group2 = group_create(groupname2, None)

        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.delete('/groups/%s/' % groupname2)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(
            Group.objects.values_list('name', flat=True).all(),
            [groupname1, groupname2]
        )


class GroupUserTests(GroupTests):
    def setUp(self):
        GroupTests.setUp(self)

        self.group1 = group_create(groupname1, self.vowi)
        self.group2 = group_create(groupname2, self.vowi)
        self.group3 = group_create(groupname3, self.vowi)
        self.group4 = group_create(groupname4, self.fsinf)
        self.group5 = group_create(groupname5, self.fsinf)


class GetUsersInGroupTests(GroupUserTests):  # GET /groups/<group>/users/
    def test_group_does_not_exist(self):
        resp = self.get('/groups/%s/users/' % groupname6)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_service_isolation(self):
        resp = self.get('/groups/%s/users/' % groupname4)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.get('/groups/%s/users/' % groupname5)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_no_users(self):
        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [])

    def test_one_user(self):
        self.group1.users.add(self.user1)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertEquals(self.parse(resp, 'list'), [username1])

    def test_two_users(self):
        self.group1.users.add(self.user1)
        self.group1.users.add(self.user2)
        self.group2.users.add(self.user3)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])

    def test_simple_inheritance(self):
        self.group1.users.add(self.user1)
        self.group1.users.add(self.user2)
        self.group2.users.add(self.user3)
        self.group1.groups.add(self.group2)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])

        # group3 has users1-3, because of inheritance
        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [username1, username2, username3])

    def test_multilevel_inheritance(self):
        self.group1.users.add(self.user1)
        self.group2.users.add(self.user2)
        self.group3.users.add(self.user3)
        self.group1.groups.add(self.group2)
        self.group2.groups.add(self.group3)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1])

        # group2 has users1-2, because of inheritance
        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(self.parse(resp, 'list'), [username1, username2])

        # similar: gorup 3 has all users:
        resp = self.get('/groups/%s/users/' % groupname3)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [username1, username2, username3])

    def test_hidden_inheritance(self):
        """
        Test a complex group-inheritance pattern.

        group 5, service=None, direct-members: user1, user2
        |- group 1, service=vowi, direct-members: user3
           |- group 4, service=fsinf, direct-members: user4
              |- group 2, service=vowi, direct-members: user5
        """
        # set up data structure:
        self.user4 = user_create(username4, password4)
        self.user5 = user_create(username5, password5)

        # group 5 has no service (hidden "global" group)
        self.group5.users.add(self.user1)
        self.group5.users.add(self.user2)
        self.group5.groups.add(self.group1)
        self.group1.users.add(self.user3)
        self.group1.groups.add(self.group4)  # group4 is fsinf service
        self.group4.users.add(self.user4)
        self.group4.groups.add(self.group2)
        self.group2.users.add(self.user5)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'), [username1, username2, username3])

        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEquals(resp.status_code, httplib.OK)
        self.assertItemsEqual(
            self.parse(resp, 'list'),
            [username1, username2, username3, username4, username5]
        )


class AddUserToGroupTests(GroupUserTests):  # POST /groups/<group>/users/
    def test_group_doesnt_exist(self):
        resp = self.post('/groups/%s/users/' % groupname6, {'user': username5})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_user_doesnt_exist(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username5})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_add_user(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(self.group1.users.all(), [self.user1])
        self.assertItemsEqual(self.group2.users.all(), [])
        self.assertItemsEqual(self.group3.users.all(), [])

    def test_add_user_twice(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(self.group1.users.all(), [self.user1])
        self.assertItemsEqual(self.group2.users.all(), [])
        self.assertItemsEqual(self.group3.users.all(), [])

        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(self.group1.users.all(), [self.user1])
        self.assertItemsEqual(self.group2.users.all(), [])
        self.assertItemsEqual(self.group3.users.all(), [])

    def test_service_isolation(self):
        resp = self.post('/groups/%s/users/' % groupname4, {'user': username1})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(
            self.get_grp(groupname4, self.fsinf).users.all(), [])

        resp = self.post('/groups/%s/users/' % groupname5, {'user': username1})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(
            self.get_grp(groupname5, self.fsinf).users.all(), [])

    def test_bad_requests(self):
        resp = self.post('/groups/%s/users/' % groupname1, {})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

        resp = self.post('/groups/%s/users/' % groupname1, {'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)

        resp = self.post(
            '/groups/%s/users/' % groupname1,
            {'user': username1, 'foo': 'bar'}
        )
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)


# GET /groups/<group>/users/<user>/
class VerifyUserInGroupTests(GroupUserTests):
    def  is_member(self, groupname, username):
        """
        Test if user is a member. Throws assertion error if the group doesn't
        exist.
        """
        resp = self.get('/groups/%s/users/%s/' % (groupname, username))
        if resp.status_code == httplib.NO_CONTENT:
            return True
        else:
            self.assertEquals(resp.status_code, httplib.NOT_FOUND)
            self.assertEqual(resp['Resource-Type'], 'user')
            return False

    def test_group_doesnt_exist(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname6, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_service_isolation(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.group4.users.add(self.user1)

        resp = self.get('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_user_doesnt_exist(self):
        resp = self.get('/groups/%s/users/%s/' % (groupname1, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_user_not_in_group(self):
        self.assertFalse(self.is_member(groupname1, username1))
        self.assertFalse(self.is_member(groupname2, username1))

    def test_user_in_group(self):
        self.group1.users.add(self.user1)

        self.assertTrue(self.is_member(groupname1, username1))
        self.assertFalse(self.is_member(groupname2, username1))

    def test_simple_inheritance(self):
        self.group1.users.add(self.user1)
        self.group2.users.add(self.user2)
        self.group1.groups.add(self.group2)

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
        self.user4 = user_create(username4, password4)
        self.user5 = user_create(username5, password5)

        # group 5 has no service (hidden "global" group)
        self.group5.users.add(self.user1)
        self.group5.users.add(self.user2)
        self.group5.groups.add(self.group1)
        self.group1.users.add(self.user3)
        self.group1.groups.add(self.group4)  # group4 is fsinf service
        self.group4.users.add(self.user4)
        self.group4.groups.add(self.group2)
        self.group2.users.add(self.user5)

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
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_user_doesnt_exist(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname1, username5))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_delete_user(self):
        self.group1.users.add(self.user1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname1, username1))
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

    def test_user_not_member(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname1, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_service_isolation(self):
        resp = self.delete('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(self.group4.users.all(), [])

        self.group4.users.add(self.user1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(self.group4.users.all(), [self.user1])

        # same as above except for global group:
        resp = self.delete('/groups/%s/users/%s/' % (groupname5, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertItemsEqual(self.group5.users.all(), [])

        self.group5.users.add(self.user1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname5, username1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(self.group5.users.all(), [self.user1])


class GetSubGroupTests(GroupUserTests):  # GET /groups/<group>/groups/
    def test_group_doesnt_exist(self):
        resp = self.get('/groups/%s/groups/' % groupname6)
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_get_no_subgroups(self):
        self.group2.groups.add(self.group4)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)

        self.assertEquals(self.parse(resp, 'list'), [])

    def test_get_one_subgroup(self):
        self.group1.groups.add(self.group2)
        self.group1.groups.add(self.group5)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)

        self.assertEquals(self.parse(resp, 'list'), [groupname2])

    def test_get_two_subgroups(self):
        self.group1.groups.add(self.group2)
        self.group1.groups.add(self.group3)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)

        self.assertEquals(self.parse(resp, 'list'), [groupname2, groupname3])

    def test_service_isolation(self):
        self.group1.groups.add(self.group2)
        self.group1.groups.add(self.group4)
        self.group1.groups.add(self.group5)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEquals(resp.status_code, httplib.OK)

        self.assertEquals(self.parse(resp, 'list'), [groupname2])


class AddSubGroupTests(GroupUserTests):  # POST /groups/<group>/groups/
    def test_group_doesnt_exist(self):
        resp = self.post(
            '/groups/%s/groups/' % groupname6, {'group': groupname1})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(Group.objects.filter(name=groupname6).exists())
        self.assertEquals(self.group1.parent_groups.all().count(), 0)

    def test_subgroup_doesnt_exist(self):
        resp = self.post(
            '/groups/%s/groups/' % groupname1, {'group': groupname6})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(Group.objects.filter(name=groupname6).exists())
        self.assertEquals(self.group1.groups.all().count(), 0)

    def test_add_subgroup(self):
        resp = self.post(
            '/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [self.group2])
        self.assertItemsEqual(self.group2.parent_groups.all(), [self.group1])

    def test_add_subgroup_twice(self):
        resp = self.post(
            '/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [self.group2])
        self.assertItemsEqual(self.group2.parent_groups.all(), [self.group1])

        resp = self.post(
            '/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [self.group2])
        self.assertItemsEqual(self.group2.parent_groups.all(), [self.group1])

    def test_bad_requests(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])

        resp = self.post('/groups/%s/groups/' % groupname1, {'foo': 'bar'})
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])

        resp = self.post(
            '/groups/%s/groups/' % groupname1,
            {'group': groupname2, 'foo': 'bar'}
        )
        self.assertEquals(resp.status_code, httplib.BAD_REQUEST)
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])

    def test_service_isolation(self):
        # we shouldn't be able to add a subgroup:
        resp = self.post(
            '/groups/%s/groups/' % groupname1, {'group': groupname4})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEquals(resp['Resource-Type'], 'group')
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])
        self.assertItemsEqual(
            self.get_grp(groupname4, self.fsinf).parent_groups.all(), [])

        # same with global group:
        resp = self.post(
            '/groups/%s/groups/' % groupname1, {'group': groupname5})
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEquals(resp['Resource-Type'], 'group')
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])
        self.assertItemsEqual(
            self.get_grp(groupname5, self.fsinf).parent_groups.all(), [])


# DELETE /groups/<group>/groups/<subgroup>/
class RemoveSubGroupTests(GroupUserTests):
    def test_group_doesnt_exist(self):
        resp = self.delete('/groups/%s/groups/%s/' % (groupname6, groupname1))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(Group.objects.filter(name=groupname6).exists())

    def test_subgroup_doesnt_exist(self):
        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname6))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(Group.objects.filter(name=groupname6).exists())

    def test_remove_subgroup(self):
        self.group1.groups.add(self.group2)
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [self.group2])
        self.assertItemsEqual(
            self.get_grp(groupname2, self.vowi).parent_groups.all(),
            [self.group1]
        )

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEquals(resp.status_code, httplib.NO_CONTENT)

        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])
        self.assertItemsEqual(
            self.get_grp(groupname2, self.vowi).parent_groups.all(), [])

    def test_remove_invalid_subgroup(self):
        # try to remove subgroup thats not really a subgroup
        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])
        self.assertItemsEqual(
            self.get_grp(groupname2, self.vowi).parent_groups.all(), [])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertItemsEqual(
            self.get_grp(groupname1, self.vowi).groups.all(), [])
        self.assertItemsEqual(
            self.get_grp(groupname2, self.vowi).parent_groups.all(), [])

    def test_service_isolation(self):
        self.group1.groups.add(self.group4)
        self.group1.groups.add(self.group5)
        group1 = self.get_grp(groupname1, self.vowi)
        self.assertItemsEqual(
            group1.groups.values_list('name', flat=True).all(),
            [groupname4, groupname5]
        )
        self.assertItemsEqual(
            self.get_grp(groupname4, self.fsinf).parent_groups.all(),
            [self.group1]
        )
        self.assertItemsEqual(
            self.get_grp(groupname5, self.fsinf).parent_groups.all(),
            [self.group1]
        )

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname4))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname5))
        self.assertEquals(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        # nothing has changed!?
        group1 = self.get_grp(groupname1, self.vowi)
        self.assertItemsEqual(
            group1.groups.values_list('name', flat=True).all(),
            [groupname4, groupname5]
        )
        self.assertItemsEqual(
            self.get_grp(groupname4, self.fsinf).parent_groups.all(),
            [self.group1]
        )
        self.assertItemsEqual(
            self.get_grp(groupname5, self.fsinf).parent_groups.all(),
            [self.group1]
        )
