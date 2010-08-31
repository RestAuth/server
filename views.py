from django.http import HttpResponse

def index( request ):
	return HttpResponse( """<html>
<head>
<title>Welcome to RestAuth</title>
</head>
<body>
Welcome to <a href="http://fs.fsinf.at/wiki/RestAuth">RestAuth</a>.
</body>
</html>""" )
