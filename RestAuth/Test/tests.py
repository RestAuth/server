"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import httplib

from RestAuth.Groups.models import Group
from RestAuth.Users.models import ServiceUser
from RestAuth.common.testdata import groupname1
from RestAuth.common.testdata import password1
from RestAuth.common.testdata import propkey1
from RestAuth.common.testdata import propval1
from RestAuth.common.testdata import propval2
from RestAuth.common.testdata import RestAuthTransactionTest
from RestAuth.common.testdata import username1


class CreateUserTest(RestAuthTransactionTest):
    def test_dry_run_create_user(self):
        resp = self.post('/test/users/', {'user': username1})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertFalse(ServiceUser.objects.all())

    def test_dry_run_create_user_with_pass(self):
        resp = self.post(
            '/test/users/', {'user': username1, 'password': password1})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertFalse(ServiceUser.objects.all())

    def test_dry_run_create_user_with_props(self):
        resp = self.post('/test/users/', {'user': username1,
                                          'properties': {'foo': 'bar'}})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertFalse(ServiceUser.objects.all())

    def test_dry_run_create_user_with_pass_and_props(self):
        content = {'user': username1, 'password': password1,
                   'properties': {'foo': 'bar'}}
        resp = self.post('/test/users/', content)
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertFalse(ServiceUser.objects.all())

    def test_dry_run_create_existing_user(self):
        user = ServiceUser.objects.create(username=username1)
        user.save()

        resp = self.post('/test/users/', {'user': username1})
        self.assertEqual(resp.status_code, httplib.CONFLICT)
        self.assertItemsEqual([user], ServiceUser.objects.all())

    def test_dry_run_create_invalid_user(self):
        resp = self.post('/test/users/', {'user': 'foo/bar'})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertFalse(ServiceUser.objects.all())

    def test_dry_run_create_short_user(self):
        resp = self.post('/test/users/', {'user': 'x'})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertFalse(ServiceUser.objects.all())

    def test_create_with_too_short_pass(self):
        resp = self.post('/test/users/', {'user': username1, 'password': 'a'})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertFalse(ServiceUser.objects.all())


class CreatePropertyTest(RestAuthTransactionTest):
    def setUp(self):
        RestAuthTransactionTest.setUp(self)
        self.user = ServiceUser.objects.create(username=username1)

    def test_create_property(self):
        url = '/test/users/%s/props/' % self.user.username
        resp = self.post(url, {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httplib.CREATED)

        self.assertFalse(self.user.property_set.all())

    def test_create_existing_property(self):
        prop = self.user.property_set.create(key=propkey1, value=propval1)

        url = '/test/users/%s/props/' % self.user.username
        resp = self.post(url, {'prop': propkey1, 'value': propval2})
        self.assertEqual(resp.status_code, httplib.CONFLICT)

        self.assertEqual(prop, self.user.property_set.get(key=propkey1))

    def test_create_invalid_property(self):
        url = '/test/users/%s/props/' % self.user.username
        resp = self.post(url, {'prop': propkey1, 'value': 'foo/bar'})
        self.assertEqual(resp.status_code, httplib.CREATED)

        self.assertFalse(self.user.property_set.all())

    def test_create_property_for_non_existing_user(self):
        url = '/test/users/%s/props/' % 'wronguser'
        resp = self.post(url, {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)

        self.assertFalse(self.user.property_set.all())

    def test_create_property_for_invalid_user(self):
        url = '/test/users/%s/props/' % 'wrong\user'
        resp = self.post(url, {'prop': propkey1, 'value': propval1})
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertFalse(self.user.property_set.all())


class CreateGroupTest(RestAuthTransactionTest):
    def test_dry_run_create_group(self):
        resp = self.post('/test/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, httplib.CREATED)
        self.assertFalse(Group.objects.all())

    def test_dry_run_create_existing_group(self):
        group = Group(name=groupname1, service=self.service)
        group.save()

        resp = self.post('/test/groups/', {'group': groupname1})
        self.assertEqual(resp.status_code, httplib.CONFLICT)
        self.assertItemsEqual([group], Group.objects.all())

    def test_dry_run_create_invalid_group(self):
        resp = self.post('/test/groups/', {'group': 'foo/bar'})
        self.assertEqual(resp.status_code, httplib.PRECONDITION_FAILED)
        self.assertFalse(Group.objects.all())
