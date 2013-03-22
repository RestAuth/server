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

from __future__ import unicode_literals  # unicode literals from python3

from django.contrib.auth.hashers import load_hashers
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.test import TransactionTestCase
from django.test.client import Client
from django.test.utils import override_settings

from RestAuthCommon import handlers

from RestAuth.Groups.models import group_permissions
from RestAuth.Services.models import service_create
from RestAuth.Users.models import prop_permissions
from RestAuth.Users.models import user_permissions
from RestAuth.backends import group_backend
from RestAuth.backends import property_backend
from RestAuth.backends import user_backend

username1 = "mati \u6111"
username2 = "mati \u6112"
username3 = "mati \u6113"
username4 = "mati \u6114"
username5 = "mati \u6115"

password1 = "password \u6121"
password2 = "password \u6122"
password3 = "password \u6123"
password4 = "password \u6124"
password5 = "password \u6125"

groupname1 = "group 1 \u6131"
groupname2 = "group 2 \u6132"
groupname3 = "group 3 \u6133"
groupname4 = "group 4 \u6134"
groupname5 = "group 5 \u6135"
groupname6 = "group 6 \u6136"
groupname7 = "group 7 \u6137"
groupname8 = "group 8 \u6138"
groupname9 = "group 9 \u6139"

propkey1 = "propkey \u6141"
propkey2 = "propkey \u6142"
propkey3 = "propkey \u6143"
propkey4 = "propkey \u6144"
propkey5 = "propkey \u6145"

propval1 = "propval \u6151"
propval2 = "propval \u6152"
propval3 = "propval \u6153"
propval4 = "propval \u6154"
propval5 = "propval \u6155"

PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher', )


class RestAuthTestBase(object):
    def setUp(self):
        if hasattr(self, 'settings'):  # requires django-1.4:
            self.settings(LOGGING_CONFIG=None)

        self.c = Client()
        self.handler = handlers.json()
        self.extra = {
            'HTTP_ACCEPT': self.handler.mime,
            'REMOTE_USER': 'vowi',
            'content_type': self.handler.mime,
        }
        self.service = service_create('vowi', 'vowi', '127.0.0.1', '::1')

        # add permissions:
        u_ct = ContentType.objects.get(app_label="Users", model="serviceuser")
        p_ct = ContentType.objects.get(app_label="Users", model="property")
        g_ct = ContentType.objects.get(app_label="Groups", model="group")

        # add user-permissions:
        for codename, name in user_permissions:
            p, c = Permission.objects.get_or_create(
                codename=codename, content_type=u_ct, defaults={'name': name})
            self.service.user_permissions.add(p)

        for codename, name in prop_permissions:
            p, c = Permission.objects.get_or_create(
                codename=codename, content_type=p_ct, defaults={'name': name})
            self.service.user_permissions.add(p)

        for codename, name in group_permissions:
            p, c = Permission.objects.get_or_create(
                codename=codename, content_type=g_ct, defaults={'name': name})
            self.service.user_permissions.add(p)

        cache.clear()

    def get(self, url, data={}):
        return self.c.get(url, data, **self.extra)

    def post(self, url, data):
        post_data = self.handler.marshal_dict(data)
        return self.c.post(url, post_data, **self.extra)

    def put(self, url, data):
        data = self.handler.marshal_dict(data)
        return self.c.put(url, data, **self.extra)

    def delete(self, url):
        return self.c.delete(url, **self.extra)

    def parse(self, response, typ):
        body = response.content.decode('utf-8')
        func = getattr(self.handler, 'unmarshal_%s' % typ)
        return func(body)

    def create_user(self, username, password=None):
        return user_backend.create(username=username, password=password,
                                  property_backend=property_backend)

    def create_group(self, service, groupname):
        return group_backend.create(name=groupname, service=service)

    def assertProperties(self, user, expected):
        actual = property_backend.list(user)
        self.assertTrue('date joined' in actual)
        del actual['date joined']
        self.assertDictEqual(actual, expected)

    def assertPassword(self, username, password):
        self.assertTrue(user_backend.check_password(username, password))

    def assertFalsePassword(self, username, password):
        self.assertFalse(user_backend.check_password(username, password))

    @classmethod
    def setUpClass(cls):
        load_hashers(('django.contrib.auth.hashers.MD5PasswordHasher', ))

    def tearDown(self):
        user_backend.testTearDown()
        group_backend.testTearDown()


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class RestAuthTest(RestAuthTestBase, TestCase):
    def assertItemsEqual(self, actual, expected, msg=None):
        """This method is not present in python3."""
        self.assertEqual(set(actual), set(expected), msg)
        self.assertEqual(len(actual), len(expected))


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class RestAuthTransactionTest(RestAuthTestBase, TransactionTestCase):
    def assertItemsEqual(self, actual, expected, msg=None):
        """This method is not present in python3."""
        self.assertEqual(set(actual), set(expected), msg)
        self.assertEqual(len(actual), len(expected))
