# This file is part of RestAuth (http://fs.fsinf.at/wiki/RestAuth).
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
from django.contrib.auth.models import User
from RestAuth.common.errors import ServiceNotFound

class ServiceUsernameNotValid( BaseException ):
	pass

class ServiceAlreadyExists( BaseException ):
	pass

def check_service_username( name ):
	if type( name ) != str:
		raise ServiceUsernameNotValid( "Name must be of type string" )
	if not name:
		raise ServiceUsernameNotValid( "Service names must be at least one character long" )
	if ':' in name:
		raise ServiceUsernameNotValid( "Service names must not contain a ':'" )

def service_create( name, password, addresses=[] ):
	check_service_username( name )
	
	if Service.objects.filter( username=name ).exists():
		raise ServiceAlreadyExists( "Service already exists. Please use a different name." )

	service = Service( username=name )
	service.set_password( password )
	service.save()

	if addresses:
		service.set_hosts( addresses )

def service_exists( name ):
	if User.objects.filter( username=name ).exists():
		return True
	else:
		return False

def service_get( name ):
	try:
		return Service.objects.get( username=name )
	except User.DoesNotExist:
		raise ServiceNotFound( "Service not found: %s"%(name) )

def service_delete( name ):
	service = service_get( name )
	service.delete()

def verify_service( name, password, host ):
	try:
		obj = Service.objects.get( username=name )

		if not obj.check_password( password ):
			return False
		return obj.verify_host( host )
	except Service.DoesNotExist:
		return None

class Service( User ):
	class Meta:
		proxy = True
	
	def verify_host( self, host ):
		if self.addresses.filter( address=host ).exists():
			return True
		else: 
			return False
	
	def set_hosts( self, addresses=[] ):
		self.addresses = []
		self.save()

		for addr in addresses:
			try:
				host = ServiceAddress.objects.get( address=addr )
			except ServiceAddress.DoesNotExist:
				host = ServiceAddress( address=addr )
				host.save()

			self.addresses.add( host )
			self.save()

	def add_host( self, address ):
		try:
			host = ServiceAddress.objects.get( address=addr )
		except ServiceAddress.DoesNotExist:
			host = ServiceAddress( address=addr )
			host.save()
		
		self.addresses.add( host )
		self.save()

	def del_host( self, address ):
		try:
			host = ServiceAddress.objects.get( address=addr )
			self.addresses.remove( host )
		except ServiceAddress.DoesNotExist:
			pass

class ServiceAddress( models.Model ):
	address = models.CharField( max_length=39, unique=True )
	services = models.ManyToManyField( User, related_name='addresses' )
