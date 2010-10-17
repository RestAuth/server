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


from django.http import HttpResponse

def sql_profiler( view, request, *args, **kwargs ):
	"""
	sql_profiler
	"""
	from django.db import connection
	connection.queries = []

	try:
		return view( request, *args, **kwargs )
	finally:
		print( '%s queries:'%(len( connection.queries )) )
		for query in connection.queries:
			print( '%s; (%s secs)'%(query['sql'], query['time']) )

def sql_profile( function = None ):
	def view_decorator(func):
		def wrapper(request, *args, **kwargs):
			return sql_profiler(func, request, *args, **kwargs)
		return wrapper
	return view_decorator
