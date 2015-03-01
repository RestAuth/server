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

from backends import backend
from common.compat import encode_str as _e
from common.testdata import CliMixin
from common.testdata import RestAuthTransactionTest
from common.testdata import capture
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
from common.testdata import username1
from common.testdata import username2
from common.testdata import username3
from common.testdata import username4
from common.testdata import username5

cli = getattr(__import__('bin.restauth-group'), 'restauth-group').main


class GroupTests(RestAuthTransactionTest):
    def setUp(self):
        super(GroupTests, self).setUp()

        # two users, so we can make sure nothing leaks to the other user
        self.create_user(username1, password1)
        self.create_user(username2, password2)
        self.create_user(username3, password3)


class GetGroupsTests(GroupTests):  # GET /groups/
    def test_get_no_groups(self):
        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_get_one_group(self):
        backend.create_group(service=self.service, name=groupname1)

        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [groupname1])

    def test_get_two_groups(self):
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service, name=groupname2)

        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1, groupname2])

    def test_service_isolation(self):
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service2, name=groupname4)
        backend.create_group(service=None, name=groupname5)

        resp = self.get('/groups/')
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1])


class GetGroupsOfUserTests(GroupTests):  # GET /groups/?user=<user>
    def test_user_doesnt_exist(self):
        resp = self.get('/groups/', {'user': username5})

        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'user')

    def test_no_memberships(self):
        # we add a group where user1 is NOT a member:
        backend.create_group(service=self.service, name=groupname1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_one_membership(self):
        backend.create_group(service=self.service, name=groupname1)
        backend.add_user(group=groupname1, service=self.service, user=username1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [groupname1])

        # test that user2 still has no memberships:
        resp = self.get('/groups/', {'user': username2})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_two_memberships(self):
        backend.create_group(service=self.service, name=groupname1)
        backend.add_user(group=groupname1, service=self.service, user=username1)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1])

        # test that user2 still has no memberships:
        resp = self.get('/groups/', {'user': username2})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [])

    def test_simple_inheritance(self):
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service, name=groupname2)
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2,
                             subservice=self.service)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1, groupname2])

    def test_multilevel_inheritance(self):
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service, name=groupname2)
        backend.create_group(service=self.service, name=groupname3)
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2,
                             subservice=self.service)
        backend.add_subgroup(group=groupname2, service=self.service, subgroup=groupname3,
                             subservice=self.service)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1, groupname2, groupname3])

    def test_interservice_inheritance(self):
        backend.create_group(service=None, name=groupname1)
        backend.create_group(service=self.service2, name=groupname2)
        backend.create_group(service=self.service, name=groupname3)
        backend.add_user(group=groupname1, service=None, user=username1)
        backend.add_subgroup(group=groupname1, service=None, subgroup=groupname2,
                             subservice=self.service2)
        backend.add_subgroup(group=groupname2, service=self.service2, subgroup=groupname3,
                             subservice=self.service)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname3])

    def test_distinct_inheritance(self):
        """
        This test checks if the call may return groups several times.
        This may occur if a user is member in several groups.
        """
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service, name=groupname2)
        backend.create_group(service=self.service, name=groupname3)

        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_user(group=groupname2, service=self.service, user=username1)
        backend.add_user(group=groupname3, service=self.service, user=username1)

        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2,
                             subservice=self.service)
        backend.add_subgroup(group=groupname2, service=self.service, subgroup=groupname3,
                             subservice=self.service)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1, groupname2, groupname3])

    def test_hidden_intermediate_dependencies(self):
        # membership to group2 is invisible, because it belongs to a different
        # service.
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service2, name=groupname2)
        backend.create_group(service=self.service, name=groupname3)
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2,
                             subservice=self.service2)
        backend.add_subgroup(group=groupname2, service=self.service2, subgroup=groupname3,
                             subservice=self.service)

        resp = self.get('/groups/', {'user': username1})
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [groupname1, groupname3])


class CreateGroupTests(GroupTests):  # POST /groups/
    def test_create_group(self):
        resp = self.post('/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertCountEqual(backend.list_groups(service=self.service), [groupname1])

    def test_create_existing_group(self):
        backend.create_group(service=self.service, name=groupname1)

        resp = self.post('/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CONFLICT)
        self.assertCountEqual(backend.list_groups(service=self.service), [groupname1])

    def test_create_group_with_users(self):
        users = [username1, username2]
        resp = self.post('/groups/', {'group': groupname1, 'users': users})
        self.assertEqual(resp.status_code, http_client.CREATED)

        self.assertCountEqual(backend.list_groups(service=self.service), [groupname1])
        self.assertCountEqual(backend.members(group=groupname1, service=self.service), users)

    def test_service_isolation(self):
        backend.create_group(service=self.service2, name=groupname1)

        resp = self.post('/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.CREATED)
        self.assertCountEqual(backend.list_groups(service=self.service), [groupname1])
        self.assertCountEqual(backend.list_groups(service=self.service2), [groupname1])

    def test_invalid_resource(self):
        resp = self.post('/groups/', {'group': 'foo\nbar'})
        self.assertEqual(resp.status_code, http_client.PRECONDITION_FAILED)
        self.assertCountEqual(backend.list_groups(service=self.service), [])


class SetGroupsTests(GroupTests):  # PUT /groups/
    def setUp(self):
        super(SetGroupsTests, self).setUp()
        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service, name=groupname2)

    def test_set_groups_for_user(self):
        group_lists = (
            [],  # also enable us to set empty list
            [groupname1],
            [groupname2],
            [groupname1, groupname2],
        )
        for group_list in group_lists:
            resp = self.put('/groups/', {'user': username1, 'groups': group_list})
            self.assertEqual(resp.status_code, http_client.NO_CONTENT)
            self.assertCountEqual(
                backend.list_groups(service=self.service, username=username1), group_list)

    def test_set_groups_with_new(self):
        self.assertFalse(backend.group_exists(name=groupname3, service=self.service))
        resp = self.put('/groups/', {'user': username1, 'groups': [groupname1, groupname3]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertCountEqual(
            backend.list_groups(service=self.service, username=username1), [groupname1, groupname3])
        self.assertTrue(backend.group_exists(name=groupname3, service=self.service))

    def test_visibility(self):
        self.assertFalse(backend.is_member(group=groupname2, service=self.service, user=username1))
        backend.create_group(service=self.service2, name=groupname3)  # different service!
        backend.add_subgroup(group=groupname3, service=self.service2, subgroup=groupname2,
                             subservice=self.service)
        backend.add_user(group=groupname3, service=self.service2, user=username1)
        self.assertTrue(backend.is_member(group=groupname3, service=self.service2, user=username1))
        self.assertTrue(backend.is_member(group=groupname2, service=self.service, user=username1))

        resp = self.put('/groups/', {'user': username1, 'groups': [groupname1]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertCountEqual(  # we still have groupname2 because it's inherited
            backend.list_groups(service=self.service, username=username1), [groupname1, groupname2])


class VerifyGroupExistanceTests(GroupTests):  # GET /groups/<group>/
    def test_does_not_exist(self):
        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_exists(self):
        backend.create_group(service=self.service, name=groupname1)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

    def test_for_leaking_services(self):
        backend.create_group(service=self.service2, name=groupname1)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_for_groups_with_no_service(self):
        backend.create_group(service=None, name=groupname1)

        resp = self.get('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')


class DeleteGroupTests(GroupTests):  # DELETE /groups/<group>/
    def test_does_not_exist(self):
        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_delete(self):
        backend.create_group(service=self.service, name=groupname1)

        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertEqual(backend.list_groups(service=self.service), [])

    def test_service_isolation(self):
        backend.create_group(service=self.service2, name=groupname1)
        backend.create_group(service=None, name=groupname2)

        resp = self.delete('/groups/%s/' % groupname1)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.delete('/groups/%s/' % groupname2)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertCountEqual(backend.list_groups(service=self.service), [])
        self.assertCountEqual(backend.list_groups(service=self.service2), [groupname1])
        self.assertCountEqual(backend.list_groups(service=None), [groupname2])


class GroupUserTests(GroupTests):
    def setUp(self):
        super(GroupUserTests, self).setUp()

        backend.create_group(service=self.service, name=groupname1)
        backend.create_group(service=self.service, name=groupname2)
        backend.create_group(service=self.service, name=groupname3)
        backend.create_group(service=self.service2, name=groupname4)
        backend.create_group(service=self.service2, name=groupname5)


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
        backend.add_user(group=groupname1, service=self.service, user=username1)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertEqual(self.parse(resp, 'list'), [username1])

    def test_two_users(self):
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_user(group=groupname1, service=self.service, user=username2)
        backend.add_user(group=groupname2, service=self.service, user=username3)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1, username2])

    def test_simple_inheritance(self):
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_user(group=groupname1, service=self.service, user=username2)
        backend.add_user(group=groupname2, service=self.service, user=username3)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1, username2])

        # group3 has users1-3, because of inheritance
        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1, username2, username3])

    def test_multilevel_inheritance(self):
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_user(group=groupname2, service=self.service, user=username2)
        backend.add_user(group=groupname3, service=self.service, user=username3)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)
        backend.add_subgroup(group=groupname2, service=self.service, subgroup=groupname3, subservice=self.service)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1])

        # group2 has users1-2, because of inheritance
        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1, username2])

        # similar: gorup 3 has all users:
        resp = self.get('/groups/%s/users/' % groupname3)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1, username2, username3])

    def test_hidden_inheritance(self):
        """
        Test a complex group-inheritance pattern.

        group 5, service=None, direct-members: user1, user2
        |- group 1, service=vowi, direct-members: user3
           |- group 4, service=fsinf, direct-members: user4
              |- group 2, service=vowi, direct-members: user5
        """
        # set up data structure:
        self.create_user(username4, password4)
        self.create_user(username5, password5)

        # group 5 has no service (hidden "global" group)
        backend.add_user(group=groupname5, service=self.service2, user=username1)
        backend.add_user(group=groupname5, service=self.service2, user=username2)
        backend.add_subgroup(group=groupname5, service=self.service2, subgroup=groupname1, subservice=self.service)
        backend.add_user(group=groupname1, service=self.service, user=username3)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4, subservice=self.service2)  # group4 is fsinf service
        backend.add_user(group=groupname4, service=self.service2, user=username4)
        backend.add_subgroup(group=groupname4, service=self.service2, subgroup=groupname2, subservice=self.service)
        backend.add_user(group=groupname2, service=self.service, user=username5)

        resp = self.get('/groups/%s/users/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'), [username1, username2, username3])

        resp = self.get('/groups/%s/users/' % groupname2)
        self.assertEqual(resp.status_code, http_client.OK)
        self.assertCountEqual(self.parse(resp, 'list'),
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

        self.assertCountEqual(backend.members(group=groupname1, service=self.service), [username1])
        self.assertCountEqual(backend.members(group=groupname2, service=self.service), [])
        self.assertCountEqual(backend.members(group=groupname3, service=self.service), [])

    def test_add_user_twice(self):
        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertCountEqual(backend.members(group=groupname1, service=self.service), [username1])
        self.assertCountEqual(backend.members(group=groupname2, service=self.service), [])
        self.assertCountEqual(backend.members(group=groupname3, service=self.service), [])

        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertCountEqual(backend.members(group=groupname1, service=self.service), [username1])
        self.assertCountEqual(backend.members(group=groupname2, service=self.service), [])
        self.assertCountEqual(backend.members(group=groupname3, service=self.service), [])

    def test_service_isolation(self):
        resp = self.post('/groups/%s/users/' % groupname4, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertCountEqual(backend.members(group=groupname4, service=self.service2), [])

        resp = self.post('/groups/%s/users/' % groupname5, {'user': username1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertCountEqual(backend.members(group=groupname5, service=self.service2), [])

    def test_bad_requests(self):
        resp = self.post('/groups/%s/users/' % groupname1, {})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)

        resp = self.post('/groups/%s/users/' % groupname1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)

        resp = self.post('/groups/%s/users/' % groupname1, {'user': username1, 'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)


class SetUsersInGroupTests(GroupUserTests):  # PUT /groups/<group>/users/
    def test_basic(self):
        usernames = (
            [],
            [username1],
            [username1, username2],
            [username1, username2, username3],
        )

        for names in usernames:
            resp = self.put('/groups/%s/users/' % groupname1, {'users': names})
            self.assertEqual(resp.status_code, http_client.NO_CONTENT)
            self.assertCountEqual(backend.members(group=groupname1, service=self.service), names)

    def test_non_existing_user(self):
        resp = self.put('/groups/%s/users/' % groupname1, {'users': [username5]})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(backend.members(group=groupname1, service=self.service), [])

    def test_service_inheritance(self):
        # user1 membership in group2 is inherited
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2,
                             subservice=self.service)
        self.assertCountEqual(backend.members(group=groupname1, service=self.service),
                              [username1])
        self.assertCountEqual(backend.members(group=groupname2, service=self.service), [username1])

        # Set user2 to group2, user1 is still member because of inheritance
        resp = self.put('/groups/%s/users/' % groupname2, {'users': [username2]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertEqual(backend.members(group=groupname2, service=self.service),
                         [username1, username2])

    def test_service_isolation(self):
        # user1 membership in group2 is inherited
        backend.create_group(name=groupname4, service=self.service)
        backend.add_user(group=groupname4, service=self.service, user=username1)
        backend.add_subgroup(group=groupname4, service=self.service, subgroup=groupname2,
                             subservice=self.service)
        self.assertCountEqual(backend.members(group=groupname4, service=self.service), [username1])
        self.assertCountEqual(backend.members(group=groupname2, service=self.service), [username1])

        resp = self.put('/groups/%s/users/' % groupname2, {'users': [username2]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertEqual(backend.members(group=groupname4, service=self.service), [username1])
        self.assertEqual(backend.members(group=groupname2, service=self.service),
                         [username1, username2])

    def test_bad_request(self):
        resp = self.put('/groups/%s/users/' % groupname1, {})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)

        resp = self.put('/groups/%s/users/' % groupname1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)

        resp = self.put('/groups/%s/users/' % groupname1, {'user': username1, 'foo': 'bar'})
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

        backend.add_user(group=groupname4, service=self.service2, user=username1)

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
        backend.add_user(group=groupname1, service=self.service, user=username1)

        self.assertTrue(self.is_member(groupname1, username1))
        self.assertFalse(self.is_member(groupname2, username1))

    def test_simple_inheritance(self):
        backend.add_user(group=groupname1, service=self.service, user=username1)
        backend.add_user(group=groupname2, service=self.service, user=username2)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)

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
        self.create_user(username4, password4)
        self.create_user(username5, password5)

        # group 5 has no service (hidden "global" group)
        backend.add_user(group=groupname5, service=self.service2, user=username1)
        backend.add_user(group=groupname5, service=self.service2, user=username2)
        backend.add_subgroup(group=groupname5, service=self.service2, subgroup=groupname1,
                             subservice=self.service)
        backend.add_user(group=groupname1, service=self.service, user=username3)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4,
                             subservice=self.service2)
        backend.add_user(group=groupname4, service=self.service2, user=username4)
        backend.add_subgroup(group=groupname4, service=self.service2, subgroup=groupname2,
                             subservice=self.service)
        backend.add_user(group=groupname2, service=self.service, user=username5)

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
        backend.add_user(group=groupname1, service=self.service, user=username1)

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
        self.assertCountEqual(backend.members(group=groupname4, service=self.service2), [])

        backend.add_user(group=groupname4, service=self.service2, user=username1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname4, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertCountEqual(backend.members(group=groupname4, service=self.service2),
                              [username1])

        # same as above except for global group:
        resp = self.delete('/groups/%s/users/%s/' % (groupname5, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertCountEqual(backend.members(group=groupname5, service=self.service2), [])

        backend.add_user(group=groupname5, service=self.service2, user=username1)

        resp = self.delete('/groups/%s/users/%s/' % (groupname5, username1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertCountEqual(backend.members(group=groupname5, service=self.service2),
                              [username1])


class GetSubGroupTests(GroupUserTests):  # GET /groups/<group>/groups/
    def test_group_doesnt_exist(self):
        resp = self.get('/groups/%s/groups/' % groupname6)
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

    def test_get_no_subgroups(self):
        backend.add_subgroup(group=groupname2, service=self.service, subgroup=groupname4, subservice=self.service2)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertEqual(self.parse(resp, 'list'), [])

    def test_get_one_subgroup(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname5, subservice=self.service2)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertEqual(self.parse(resp, 'list'), [groupname2])

    def test_get_two_subgroups(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname3, subservice=self.service)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertCountEqual(self.parse(resp, 'list'), [groupname2, groupname3])

    def test_service_isolation(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4, subservice=self.service2)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname5, subservice=self.service2)

        resp = self.get('/groups/%s/groups/' % groupname1)
        self.assertEqual(resp.status_code, http_client.OK)

        self.assertEqual(self.parse(resp, 'list'), [groupname2])


class AddSubGroupTests(GroupUserTests):  # POST /groups/<group>/groups/
    def test_group_doesnt_exist(self):
        resp = self.post('/groups/%s/groups/' % groupname6, {'group': groupname1})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(backend.group_exists(name=groupname6, service=self.service))
        subgroups = backend.subgroups(group=groupname1, service=self.service, filter=True)
        self.assertEqual(subgroups, [])

    def test_subgroup_doesnt_exist(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname6})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(backend.group_exists(name=groupname6, service=self.service))
        self.assertCountEqual(backend.subgroups(group=groupname1, service=self.service), [])

    def test_add_subgroup(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False),
            [(groupname2, self.service)])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service),
                              [(groupname1, self.service)])

    def test_add_subgroup_twice(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False),
            [(groupname2, self.service)])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service),
                              [(groupname1, self.service)])

        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False),
            [(groupname2, self.service)])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service),
                              [(groupname1, self.service)])

    def test_bad_requests(self):
        resp = self.post('/groups/%s/groups/' % groupname1, {})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])

        resp = self.post('/groups/%s/groups/' % groupname1, {'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])

        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname2, 'foo': 'bar'})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])

    def test_service_isolation(self):
        # we shouldn't be able to add a subgroup:
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname4})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])
        self.assertCountEqual(backend.parents(group=groupname4, service=self.service2), [])

        # same with global group:
        resp = self.post('/groups/%s/groups/' % groupname1, {'group': groupname5})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])
        self.assertCountEqual(backend.parents(group=groupname5, service=self.service2), [])


class SetSubgroupsTests(GroupUserTests):  # PUT /groups/<group>/groups/
    def test_basic(self):
        resp = self.put('/groups/%s/groups/' % groupname1, {'groups': [groupname2]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertCountEqual(backend.subgroups(group=groupname1, service=self.service),
                              [groupname2])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service),
                              [(groupname1, self.service)])

        resp = self.put('/groups/%s/groups/' % groupname1, {'groups': []})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertCountEqual(backend.subgroups(group=groupname1, service=self.service), [])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service), [])

        resp = self.put('/groups/%s/groups/' % groupname1,
                        {'groups': [groupname2, groupname3]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertCountEqual(backend.subgroups(group=groupname1, service=self.service),
                              [groupname2, groupname3])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service),
                              [(groupname1, self.service)])
        self.assertCountEqual(backend.parents(group=groupname3, service=self.service),
                              [(groupname1, self.service)])

    def test_metagroup_not_found(self):
        resp = self.put('/groups/%s/groups/' % groupname6, {'groups': [groupname2]})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service), [])

    def test_subgroup_not_found(self):
        resp = self.put('/groups/%s/groups/' % groupname1, {'groups': [groupname6]})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertCountEqual(backend.subgroups(group=groupname1, service=self.service), [])

    def test_service_isolation(self):
        # test adding a subgroup of a different service
        resp = self.put('/groups/%s/groups/' % groupname1, {'groups': [groupname4]})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertCountEqual(
            backend.subgroups(group=groupname1, service=self.service, filter=False), [])

        # test the other way round
        resp = self.put('/groups/%s/groups/' % groupname4, {'groups': [groupname1]})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertCountEqual(
            backend.subgroups(group=groupname1, service=self.service, filter=False), [])

        # test adding within a different service (self.put uses self.service)
        resp = self.put('/groups/%s/groups/' % groupname4, {'groups': [groupname5]})
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertCountEqual(
            backend.subgroups(group=groupname1, service=self.service, filter=False), [])

        # establich a cross-service relation, try to overwrite it:
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4, subservice=self.service2)
        resp = self.put('/groups/%s/groups/' % groupname1, {'groups': [groupname2]})
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)
        self.assertCountEqual(
            backend.subgroups(group=groupname1, service=self.service, filter=False),
            [(groupname2, self.service), (groupname4, self.service2)])

    def test_bad_request(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4, subservice=self.service2)
        resp = self.put('/groups/%s/groups/' % groupname1, {'foo': [groupname2]})
        self.assertEqual(resp.status_code, http_client.BAD_REQUEST)


class VerifySubgroupTests(GroupUserTests):  # GET /groups/<group>/groups/<subgroup>/
    def test_basic(self):
        resp = self.get('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2, subservice=self.service)
        resp = self.get('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

    def test_metagroup_doesnt_exist(self):
        resp = self.get('/groups/%s/groups/%s/' % (groupname6, groupname2))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

    def test_subgroup_doesnt_exist(self):
        resp = self.get('/groups/%s/groups/%s/' % (groupname1, groupname6))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)

    def test_service_isolation(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4, subservice=self.service2)
        resp = self.get('/groups/%s/groups/%s/' % (groupname1, groupname4))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)


# DELETE /groups/<group>/groups/<subgroup>/
class RemoveSubGroupTests(GroupUserTests):
    def test_group_doesnt_exist(self):
        resp = self.delete('/groups/%s/groups/%s/' % (groupname6, groupname1))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(backend.group_exists(name=groupname6, service=self.service))
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])

    def test_subgroup_doesnt_exist(self):
        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname6))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertFalse(backend.group_exists(name=groupname6, service=self.service))
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])

    def test_remove_subgroup(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname2,
                             subservice=self.service)
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [(groupname2, self.service)])
        self.assertCountEqual(
            backend.parents(group=groupname2, service=self.service),
            [(groupname1, self.service)])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEqual(resp.status_code, http_client.NO_CONTENT)

        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])
        self.assertCountEqual(backend.parents(group=groupname2, service=self.service), [])

    def test_remove_invalid_subgroup(self):
        # try to remove subgroup thats not really a subgroup
        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])
        self.assertCountEqual(backend.subgroups(
            group=groupname2, service=self.service, filter=False), [])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname2))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        self.assertCountEqual(backend.subgroups(
            group=groupname1, service=self.service, filter=False), [])
        self.assertCountEqual(backend.subgroups(
            group=groupname2, service=self.service, filter=False), [])

    def test_service_isolation(self):
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname4,
                             subservice=self.service2)
        backend.add_subgroup(group=groupname1, service=self.service, subgroup=groupname5,
                             subservice=self.service2)
        self.assertCountEqual(
            backend.subgroups(group=groupname1, service=self.service, filter=False),
            [(groupname4, self.service2), (groupname5, self.service2)])
        self.assertCountEqual(backend.parents(group=groupname4, service=self.service2),
                              [(groupname1, self.service)])
        self.assertCountEqual(backend.parents(group=groupname5, service=self.service2),
                              [(groupname1, self.service)])

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname4))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        resp = self.delete('/groups/%s/groups/%s/' % (groupname1, groupname5))
        self.assertEqual(resp.status_code, http_client.NOT_FOUND)
        self.assertEqual(resp['Resource-Type'], 'group')

        # nothing has changed!?
        self.assertCountEqual(
            backend.subgroups(group=groupname1, service=self.service, filter=False),
            [(groupname4, self.service2), (groupname5, self.service2)])
        self.assertCountEqual(backend.parents(group=groupname4, service=self.service2),
                              [(groupname1, self.service)])
        self.assertCountEqual(backend.parents(group=groupname5, service=self.service2),
                              [(groupname1, self.service)])


class CliTests(RestAuthTransactionTest, CliMixin):
    def test_add(self):
        with capture() as (stdout, stderr):
            cli(['add', groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(backend.group_exists(groupname1))

        with capture() as (stdout, stderr):
            cli(['add', '--service=%s' % self.service.username, groupname2 if six.PY3 else
                 groupname2.encode('utf-8')])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertTrue(backend.group_exists(groupname2, service=self.service))

    def test_add_exists(self):
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname2, service=self.service)

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
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname2)
        backend.create_group(name=groupname3, service=self.service)
        backend.create_group(name=groupname4, service=self.service)

        with capture() as (stdout, stderr):
            cli(['ls'])
            self.assertEqual(stdout.getvalue(), '%s\n%s\n' % (groupname1, groupname2))
            self.assertEqual(stderr.getvalue(), '')

        with capture() as (stdout, stderr):
            cli(['ls', '--service=%s' % self.service.username])
            self.assertEqual(stdout.getvalue(), '%s\n%s\n' % (groupname3, groupname4))
            self.assertEqual(stderr.getvalue(), '')

    def test_view(self):
        backend.create_user(username1)
        backend.create_user(username2)
        backend.create_user(username3)
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname2)
        backend.create_group(name=groupname3)
        backend.create_group(groupname4, service=self.service)
        backend.create_group(groupname5, service=self.service)

        with capture() as (stdout, stderr):
            cli(['view', groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stderr.getvalue(), '')
            self.assertEqual(stdout.getvalue(), """* No explicit members
* No effective members
* No parent groups
* No subgroups
""")

        # add a few members, and subgroups:
        backend.add_user(group=groupname1, service=None, user=username1)
        backend.add_user(group=groupname1, service=None, user=username2)
        backend.add_user(group=groupname4, service=self.service, user=username3)
        backend.add_subgroup(group=groupname1, service=None, subgroup=groupname2, subservice=None)
        backend.add_subgroup(group=groupname1, service=None, subgroup=groupname4,
                             subservice=self.service)
        backend.add_subgroup(group=groupname5, service=self.service, subgroup=groupname4,
                             subservice=self.service)

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
        backend.create_group(name=groupname1)

        with capture() as (stdout, stderr):
            cli(['set-service', groupname1 if six.PY3 else groupname1.encode('utf-8'),
                 self.service.username])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.list_groups(service=self.service), [groupname1])

        with capture() as (stdout, stderr):
            cli(['set-service', '--service=%s' % self.service.username,
                 groupname1 if six.PY3 else groupname1.encode('utf-8')])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.list_groups(service=None), [groupname1])

        with capture() as (stdout, stderr):  # test a non-existing group
            try:
                cli(['set-service', '--service=%s' % self.service.username,
                     groupname1 if six.PY3 else groupname1.encode('utf-8')])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: %s at service %s: Group does not exist\.$' %
                                   (groupname1, self.service.username))
        self.assertEqual(backend.list_groups(service=None), [groupname1])

    def test_add_user(self):
        backend.create_user(username1)
        backend.create_user(username2)
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname2, service=self.service)

        with capture() as (stdout, stderr):
            cli(['add-user',
                 groupname1 if six.PY3 else groupname1.encode('utf-8'),
                 username1 if six.PY3 else username1.encode('utf-8'),
            ])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.members(group=groupname1, service=None), [username1])

        with capture() as (stdout, stderr):
            cli(['add-user', '--service=%s' % self.service.username,
                 groupname2 if six.PY3 else groupname2.encode('utf-8'),
                 username2 if six.PY3 else username2.encode('utf-8'),
            ])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.members(group=groupname2, service=self.service), [username2])

    def test_add_group_neither(self):  # neither group is in any service
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname2)

        with capture() as (stdout, stderr):
            cli(['add-group',
                 groupname1 if six.PY3 else groupname1.encode('utf-8'),
                 groupname2 if six.PY3 else groupname2.encode('utf-8'),
            ])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.subgroups(group=groupname1, service=None), [groupname2])

    def test_add_group_both(self):  # bout groups are in service
        backend.create_group(name=groupname1, service=self.service)
        backend.create_group(name=groupname2, service=self.service)

        with capture() as (stdout, stderr):
            cli(['add-group', '--service=%s' % self.service.username,
                 '--sub-service=%s' % self.service.username, _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.subgroups(group=groupname1, service=self.service), [groupname2])

    def test_rename(self):
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname3)
        backend.create_group(name=groupname1, service=self.service)

        with capture() as (stdout, stderr):
            cli(['rename', _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.list_groups(service=None), [groupname2, groupname3])

        with capture() as (stdout, stderr):
            cli(['rename', '--service=%s' % self.service.username, _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.list_groups(service=self.service), [groupname2])

        # test a failed rename
        with capture() as (stdout, stderr):
            try:
                cli(['rename', _e(groupname3), _e(groupname2)])  # groupname2 already exists
                self.fail("Rename doesn't fail")
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(stderr, 'error: %s: Group already exists\.$' % groupname2)
        self.assertEqual(backend.list_groups(service=None), [groupname2, groupname3])

    def test_rm(self):
        backend.create_group(name=groupname1)
        with capture() as (stdout, stderr):
            cli(['rm', _e(groupname1)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.list_groups(service=None), [])

    def test_rm_user(self):
        backend.create_group(name=groupname1)
        backend.create_user(username1)
        backend.add_user(group=groupname1, service=None, user=username1)
        self.assertEqual(backend.members(group=groupname1, service=None), [username1])

        with capture() as (stdout, stderr):
            cli(['rm-user', _e(groupname1), _e(username1)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.members(group=groupname1, service=None), [])

        with capture() as (stdout, stderr):
            try:
                cli(['rm-user', _e(groupname1), _e(username1)])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    'error: User "%s" not member of group "%s"\.$' % (username1, groupname1))
        self.assertEqual(backend.members(group=groupname1, service=None), [])

    def test_rm_group(self):
        backend.create_group(name=groupname1)
        backend.create_group(name=groupname2)
        backend.add_subgroup(group=groupname1, service=None, subgroup=groupname2, subservice=None)
        self.assertEqual(backend.subgroups(group=groupname1, service=None), [groupname2])

        with capture() as (stdout, stderr):
            cli(['rm-group', _e(groupname1), _e(groupname2)])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(backend.subgroups(group=groupname1, service=None), [])

        with capture() as (stdout, stderr):
            try:
                cli(['rm-group', _e(groupname1), _e(groupname2)])
            except SystemExit as e:
                self.assertEqual(e.code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertHasLine(
                    stderr,
                    'error: Group "%s" is not a subgroup of "%s"\.$' % (groupname2, groupname1))
        self.assertEqual(backend.subgroups(group=groupname1, service=None), [])
