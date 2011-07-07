from argparse import ArgumentParser, Action
import argparse, re

class PasswordGenerator( Action ):
	def __call__( self, parser, namespace, values, option_string ):
		passwd = ''.join( random.choice( string.printable ) for x in range(30) )
		print( passwd )
		setattr( namespace, self.dest, passwd )

pwd_parser = ArgumentParser( add_help=False )
pwd_group = pwd_parser.add_mutually_exclusive_group()
pwd_group.add_argument( '--password', dest='pwd', metavar='PWD', help="The password to use." )
pwd_group.add_argument( '--gen-password', action=PasswordGenerator, nargs=0, dest='pwd',
	help="Generate a password and print it to stdout." )

####################################
### Various positional arguments ###
####################################
service_arg_parser = ArgumentParser(add_help=False)
service_arg_parser.add_argument( 'service', help="The name of the service." )

host_arg_parser = ArgumentParser( add_help=False )
host_arg_parser.add_argument( 'hosts', metavar='host', nargs='*', help="""A host that the service is able to
	connect from. You can name multiple hosts as additional positional arguments. If ommitted,
	this service cannot be used from anywhere.""")
username_arg_parser = ArgumentParser(add_help=False)
username_arg_parser.add_argument( 'username', help="The name of the user." )

group_arg_parser = ArgumentParser(add_help=False)
group_arg_parser.add_argument( 'group', help="The name of the group." )
group_arg_parser.add_argument( '--service', help="""Act as if %(prog)s was the service named
SERVICE. If ommitted, act on groups that are not associated with any service.""" )

subgroup_parser = ArgumentParser(add_help=False)
subgroup_parser.add_argument( 'subgroup', help="The name of the subgroup.")
subgroup_parser.add_argument( '--sub-service', metavar='SUBSERVICE',
	help="""Assume that the named subgroup is from SUBSERVICE.""")

###############################
### restauth-service parser ###
###############################
service_desc = """%(prog)s manages services in RestAuth. Services are websites, hosts, etc. that use
RestAuth as authentication service."""
service_parser = ArgumentParser( description=service_desc )

service_subparsers = service_parser.add_subparsers( title="Available actions", dest='action',
	description="""Use '%(prog)s action --help' for more help on each action.""" )
service_subparsers.add_parser( 'add', help="Add a new service.",  description="Add a new service.",
	parents=[service_arg_parser, host_arg_parser, pwd_parser] )
service_subparsers.add_parser( 'ls', help="List all services.",
	description="""List all available services.""")
service_subparsers.add_parser( 'rm', help="Remove a service.", parents=[service_arg_parser],
	description="""Completely remove a service. This will also remove any groups associated with
that service.""" )
service_subparsers.add_parser( 'view', help="View details of a service.", parents=[service_arg_parser],
	description="View details of a service." )
service_subparsers.add_parser( 'view', help="View details of a service.", parents=[service_arg_parser],
	description="View details of a service." )
service_subparsers.add_parser( 'set-hosts', parents=[service_arg_parser, host_arg_parser],
	help="Set hosts that a service can connect from.",
	description="Set hosts that a service can connect from." )
service_subparsers.add_parser( 'set-password', parents=[service_arg_parser, pwd_parser],
	help="Set the password for a service.", description="Set the password for a service." )


############################
### restauth-user parser ###
############################
user_desc = """Manages users in RestAuth. Users are clients that want to authenticate with services
that use RestAuth."""
user_parser = ArgumentParser( description=user_desc )

user_subparsers = user_parser.add_subparsers( title="Available actions", dest='action',
	description="""Use '%(prog)s action --help' for more help on each action.""" )
user_subparsers.add_parser( 'add', help="Add a new user.",
	parents=[username_arg_parser, pwd_parser],
	description="Add a new user." )
user_subparsers.add_parser( 'list', help="List all users.", description="List all users." )
user_subparsers.add_parser( 'verify', help="Verify a users password.",
	parents=[username_arg_parser, pwd_parser],
	description="Verify the password of a user." ) 
user_subparsers.add_parser( 'set-password', help="Set the password of a user.",
	parents=[username_arg_parser, pwd_parser],
	description="Set the password of a user." )
user_subparsers.add_parser( 'rm', help="Remove a user.", parents=[username_arg_parser],
	description="Remove a user." )

user_view_p = user_subparsers.add_parser( 'view', help="View details of a user.",
	parents=[username_arg_parser ], description="View details of a user." )
user_view_p.add_argument( '--service', help="View information as SERVICE would see it." )

#############################
### restauth-group parser ###
#############################
group_desc = """%(prog)s manages groups in RestAuth. Groups can have users and groups as members, handing
down users to member groups. For a group to be visible to a service, it must be associated with it.
It is possible for a group to not be associated with any service, which is usefull for e.g. a group
containing global super-users. Valid actions are help, add, list, view, add-user, add-group, remove,
remove-user, and remove-group."""
group_parser = ArgumentParser( description=group_desc )

group_subparsers = group_parser.add_subparsers( title="Available actions", dest='action',
	description="""Use '%(prog)s action --help' for more help on each action.""" )
group_subparsers.add_parser( 'add', help="Add a new group.", parents=[group_arg_parser],
	description="Add a new group." )
group_subparsers.add_parser( 'list', help="List all groups.", description="List all groups." )
group_subparsers.add_parser( 'view', help="View details of a group.", parents=[group_arg_parser],
	description="View details of a group." )
group_subparsers.add_parser( 'add-user', parents=[group_arg_parser, username_arg_parser],
	help="Add a user to a group.", description="Add a user to a group." )
group_subparsers.add_parser( 'add-group', parents=[group_arg_parser, subgroup_parser],
	help="""Make a group a subgroup to another group.""",
	description="""Make a group a subgroup of another group. The subgroup will inherit all
		memberships from the parent group.""" )
group_subparsers.add_parser( 'rm-user', parents=[group_arg_parser, username_arg_parser],
	help="Remove a user from a group.", description="Remove a user from a group." )
group_subparsers.add_parser( 'rm-group', parents=[group_arg_parser, subgroup_parser],
	help="""Remove a subgroup from a group.""",
	description="""Remove a subgroup from a group. The subgroup will no longer inherit all
		memberships from a parent group.""" )
group_subparsers.add_parser( 'rm', parents=[group_arg_parser], help="Remove a group.",
	description="Remove a group." )

########################
### helper functions ###
########################
def _metavar_formatter( action, default_metavar ):
	if action.metavar is not None:
		result = action.metavar
	elif action.choices is not None:
		choice_strs = [str(choice) for choice in action.choices]
		result = '{%s}' % ','.join(choice_strs)
	else:
		result = default_metavar
	
	def format(tuple_size):
		if isinstance(result, tuple):
		    return result
		else:
		    return (result, ) * tuple_size
	return format

def _format_args( action, default_metavar ):
	OPTIONAL = '?'
	ZERO_OR_MORE = '*'
	ONE_OR_MORE = '+'
	PARSER = 'A...'
	REMAINDER = '...'
	
	get_metavar = _metavar_formatter(action, default_metavar)
	if action.nargs is None:
		result = '*%s*' % get_metavar(1)
	elif action.nargs == OPTIONAL:
		result = '[*%s*]' % get_metavar(1)
	elif action.nargs == ZERO_OR_MORE:
		result = '[*%s* [*%s* ...]]' % get_metavar(2)
	elif action.nargs == ONE_OR_MORE:
		result = '*%s* [*%s* ...]' % get_metavar(2)
	elif action.nargs == REMAINDER:
		result = '...'
	elif action.nargs == PARSER:
		result = '%s ...' % get_metavar(1)
	else:
		formats = ['%s' for _ in range(action.nargs)]
		result = ' '.join(formats) % get_metavar(action.nargs)
	return result

def format_man_usage( parser ):
	"""
	Get a man-page compatible usage string. This function and its nested functions are mostly
	directly copied from the argparse module.
	"""
	opts = []
	args = []
	
	for action in parser._actions:
		if action.option_strings:
			opts.append( action )
		else:
			args.append( action )
	actions = opts + args
	
	group_actions = set()
	inserts = {}
	for group in parser._mutually_exclusive_groups:
		try:
			start = actions.index(group._group_actions[0])
		except ValueError:
			continue
		else:
			end = start + len(group._group_actions)
			if actions[start:end] == group._group_actions:
				for action in group._group_actions:
					group_actions.add(action)
				if not group.required:
					inserts[start] = '['
					inserts[end] = ']'
				else:
					inserts[start] = '('
					inserts[end] = ')'
				for i in range(start + 1, end):
					inserts[i] = '|'
	
	parts = []
	for i, action in enumerate( opts + args ):
		if action.help is argparse.SUPPRESS:
			parts.append(None)
			if inserts.get(i) == '|':
				inserts.pop(i)
			elif inserts.get(i + 1) == '|':
				inserts.pop(i + 1)
		elif not action.option_strings: # args
			part = _format_args(action, action.dest)
			
			# if it's in a group, strip the outer []
			if action in group_actions:
				if part[0] == '[' and part[-1] == ']':
					part = part[1:-1]

			# add the action string to the list
			parts.append(part)
		else:
			option_string = action.option_strings[0]
			
			# if the Optional doesn't take a value, format is:
			#    -s or --long
			if action.nargs == 0:
				part = '**%s**' % option_string

			# if the Optional takes a value, format is:
			#    -s ARGS or --long ARGS
			else:
				default = action.dest.upper()
				args_string = _format_args(action, default)
				part = '**%s** %s' % (option_string, args_string)
			
			# make it look optional if it's not required or in a group				
			if not action.required and action not in group_actions:
				part = '[%s]' % part
				
			parts.append( part )

	for i in sorted(inserts, reverse=True):
		parts[i:i] = [inserts[i]]
		
	text = ' '.join([item for item in parts if item is not None])
	
	# clean up separators for mutually exclusive groups
	open = r'[\[(]'
	close = r'[\])]'
	text = re.sub(r'(%s) ' % open, r'\1', text)
	text = re.sub(r' (%s)' % close, r'\1', text)
	text = re.sub(r'%s *%s' % (open, close), r'', text)
	text = re.sub(r'\(([^|]*)\)', r'\1', text)
	text = text.strip()
	
	return ' %s'%text

def write_commands( parser, cmd ):
	f = open( 'doc/includes/%s-commands.rst'%cmd, 'w' )
	commands = sorted( parser._subparsers._actions[1].choices )
	format_dict = { 'prog': parser.prog }
	for sub_cmd in commands:
		# TODO: cleanup mess in HTML output
		subparser = parser._subparsers._actions[1].choices[sub_cmd]
		subparser.prog = '%s %s'%(cmd, sub_cmd)
		
		f.write( '.. only:: not man\n')
		f.write( '   \n' )
		f.write( "   %s\n"%sub_cmd )
		f.write( '   %s\n\n'%('^'*(len(sub_cmd))) )
		f.write( '   \n' )
		
		f.write( '.. example:: ')
		header = '**%s**%s\n'%(sub_cmd, format_man_usage( subparser ) )
		f.write( header )
		f.write( '   \n')
		f.write( '   %s\n'%( ' '.join( subparser.description.split() ) ) )
		f.write( '   \n')
		
		opts = []
		args = []
		
		for action in subparser._positionals._actions:
			if type( action ) == argparse._HelpAction:
				continue
			if not action.option_strings:
				args.append( action )
			else:
				if action.metavar:
					metavar = action.metavar
				else:
					metavar = action.dest.upper()
					
				if action.nargs is None:
					strings = [ '%s %s'%(name, metavar) for name in action.option_strings ]
					option_string = ', '.join( strings )
				elif action.metavar:
					strings = [ '%s %s'%(name, action.metavar) for name in action.option_strings ]
					option_string = ', '.join( strings )
				elif action.nargs == 0:
					option_string = ', '.join( action.option_strings )
				else:
					strings = [ '%s %s'%(name, action.dest) for name in action.option_strings ]
					option_string = ', '.join( strings )
					
				
				help = ' '.join( action.help.split() )%format_dict
				opts.append( (option_string, help ) )
				
		if opts or args:
			f.write( '   .. program:: %s-%s\n\n'%(cmd, sub_cmd) ) 
				
		for opt_str, opt_desc in opts:
			f.write( '   .. option:: %s\n'%opt_str.strip() )
			f.write( '      \n')
			f.write( '      %s\n'%opt_desc)
			f.write( '      \n')
			
		for arg in args:
			arg_str = arg.dest
			arg_desc = arg.help
			f.write( '   .. option:: %s\n'%arg.dest )
			f.write( '      \n')
			help = ' '.join( arg.help.split() )
			f.write( '      %s\n'%help)
			f.write( '      \n')
		
	f.close()

def write_usage( parser, cmd ):
	f = open( 'doc/includes/%s-usage.rst'%cmd, 'w' )
	usage = parser.format_usage().replace( 'usage: ', '' )
	f.write( ' '.join( usage.split() ) )
	f.close()