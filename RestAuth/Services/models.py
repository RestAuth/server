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

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import importlib


SERVICE_HASHER = None


def load_service_hasher():
    global SERVICE_HASHER

    backend = getattr(settings, 'SERVICE_PASSWORD_HASHER', 'default')

    if backend == 'default':
        backend = settings.PASSWORD_HASHERS[0]
    elif backend not in settings.PASSWORD_HASHERS:
        raise ImproperlyConfigured("SERVICE_PASSWORD_HASHER not in PASSWORD_HASHERS")

    try:
        mod_path, cls_name = backend.rsplit('.', 1)
        mod = importlib.import_module(mod_path)
        hasher_cls = getattr(mod, cls_name)
    except (AttributeError, ImportError, ValueError) as e:
        raise ImproperlyConfigured("hasher not found: %s" % backend)
    SERVICE_HASHER = hasher_cls()


def get_service_hasher():
    if SERVICE_HASHER is None:
        load_service_hasher()
    return SERVICE_HASHER


class ServiceUsernameNotValid(BaseException):
    pass


def check_service_username(name):
    if ':' in name:
        raise ServiceUsernameNotValid("Service name must not contain a ':'")


def service_create(name, password, *hosts):
    """
    :raises IntegrityError: If the service already exists.
    """
    check_service_username(name)

    service = Service(username=name)
    service.set_password(password)
    service.save()

    # add hosts
    if hosts:
        service.add_hosts(*hosts)

    return service


class Service(User):
    class Meta:
        proxy = True

    @property
    def name(self):
        """The name of this service, actually an alias for username."""
        return self.username

    @name.setter
    def name(self, value):  # pragma: no cover
        self.username = value

    def set_password(self, raw_password):
        self.password = make_password(raw_password, hasher=get_service_hasher())

    def check_password(self, raw_password):
        def setter(raw_password):
            self.set_password(raw_password)
            self.save()
        return check_password(raw_password, self.password, setter,
                              preferred=get_service_hasher())

    def verify(self, password, host):
        if self.check_password(password) and self.verify_host(host):
            return True
        else:
            return False

    def verify_host(self, host):
        if self.hosts.filter(address=host).exists():
            return True
        else:
            return False

    def set_hosts(self, *raw_hosts):
        self.hosts.clear()
        self.add_hosts(*raw_hosts)

    def add_hosts(self, *raw_hosts):
        cleaned_hosts = [h.strip(', ') for h in raw_hosts]
        hosts = []
        for raw_host in cleaned_hosts:
            try:
                host = ServiceAddress.objects.get(address=raw_host)
            except ServiceAddress.DoesNotExist:
                host = ServiceAddress(address=raw_host)
                host.clean_fields()
                host.save()
            hosts.append(host)

        self.hosts.add(*hosts)

    def del_hosts(self, *raw_hosts):
        hosts = []
        for raw_host in raw_hosts:
            host = raw_host.strip(', ')
            try:
                hosts.append(ServiceAddress.objects.get(address=host))
            except ServiceAddress.DoesNotExist:
                pass
        self.hosts.remove(*hosts)

    @property
    def addresses(self):
        return self.hosts.values_list('address', flat=True).order_by('address')

    @property
    def permissions(self):
        return self.user_permissions.values_list('codename', flat=True).order_by('codename')

class ServiceAddress(models.Model):
    address = models.GenericIPAddressField(unique=True)
    services = models.ManyToManyField(User, related_name='hosts')

    def __unicode__(self):  # pragma: no cover
        return self.address
