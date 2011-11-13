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
from django.contrib.auth.models import User

class ServiceUsernameNotValid( BaseException ):
	pass

def check_service_username( name ):
	if ':' in name:
		raise ServiceUsernameNotValid( "Service name must not contain a ':'" )

def service_create( name, password, addresses=[] ):
	"""
	@raises IntegrityError: If the service already exists.
	"""
	check_service_username( name )
	
	service = Service( username=name )
	service.set_password( password )
	service.save()

	if addresses:
		service.set_hosts( addresses )
		
	return service

class ServiceAddress( models.Model ):
	address = models.CharField( max_length=39, unique=True )

	def __unicode__( self ): # pragma: no cover
		return self.address

class Service( User ):
	hosts = models.ManyToManyField( ServiceAddress )
	
	def verify( self, password, host ):
		if self.check_password( password ) and self.verify_host( host ):
			return True
		else:
			return False

	def verify_host( self, host ):
		if self.hosts.filter( address=host ).exists():
			return True
		else: 
			return False

	def set_hosts( self, addresses=[] ):
		self.hosts.clear()

		for addr in addresses:
			self.add_host( addr )

	def add_host( self, address ):
		addr = ServiceAddress.objects.get_or_create( address=address )[0]
		self.hosts.add( addr )

	def del_host( self, address ):
		try:
			host = ServiceAddress.objects.get( address=addr )
			self.hosts.remove( host )
		except ServiceAddress.DoesNotExist:
			pass

