from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ServiceAddress( models.Model ):
	address = models.CharField( max_length=39, unique=True )
	services = models.ManyToManyField( User )
