from django.db import models
from django.contrib.auth.models import User
from RestAuth.common import ServiceNotFound

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

class Service( User ):
	class Meta:
		proxy = True
	
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
