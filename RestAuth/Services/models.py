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

from django.db import models
from django.db.utils import IntegrityError
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType


class ServiceUsernameNotValid(BaseException):
    pass


def check_service_username(name):
    if ':' in name:
        raise ServiceUsernameNotValid("Service name must not contain a ':'")


def service_create(name, password, *hosts):
    """
    @raises IntegrityError: If the service already exists.
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
        hosts = [ServiceAddress.objects.get_or_create(address=raw)[0]
                 for raw in raw_hosts]
        self.hosts.clear()
        self.hosts.add(*hosts)

    def add_hosts(self, *raw_hosts):
        hosts = [ServiceAddress.objects.get_or_create(address=raw)[0]
                 for raw in raw_hosts]
        self.hosts.add(*hosts)

    def del_hosts(self, *raw_hosts):
        hosts = []
        for raw_host in raw_hosts:
            try:
                hosts.append(ServiceAddress.objects.get(address=raw_host))
            except ServiceAddress.DoesNotExist:
                pass
        self.hosts.remove(*hosts)

    def add_permissions(self, permissions):
        self.user_permissions.add(*permissions)

    def rm_permissions(self, permissions):
        self.user_permissions.remove(*permissions)

    def set_permissions(self, permissions):
        self.user_permissions.clear()
        self.user_permissions.add(*permissions)


class ServiceAddress(models.Model):
    address = models.CharField(max_length=39, unique=True)
    services = models.ManyToManyField(Service, related_name='hosts')

    def __unicode__(self):  # pragma: no cover
        return self.address
