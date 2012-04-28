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

from argparse import ArgumentParser, Action
import argparse, re, sys, random, string

from RestAuth.Users.models import user_permissions, prop_permissions
from RestAuth.Groups.models import group_permissions

class PasswordGenerator(Action):
    def __call__(self, parser, namespace, values, option_string):
        chars = string.digits + string.letters + string.punctuation
        chars = chars.translate(None, '\\\'"')
            
        passwd = ''.join(random.choice(chars) for x in range(30))
        print(passwd)
        setattr(namespace, self.dest, passwd)

pwd_parser = ArgumentParser(add_help=False)
pwd_group = pwd_parser.add_mutually_exclusive_group()
pwd_group.add_argument('--password', dest='pwd', metavar='PWD', help="The password to use.")
pwd_group.add_argument('--gen-password', action=PasswordGenerator, nargs=0, dest='pwd',
    help="Generate a password and print it to stdout.")

permission_list = [p[0] for p in user_permissions] +\
    [p[0] for p in prop_permissions] +\
    [p[0] for p in group_permissions]
perms = ', '.join(permission_list)

####################################
### Various positional arguments ###
####################################
service_arg_parser = ArgumentParser(add_help=False)
service_arg_parser.add_argument('service', metavar="SERVICE", help="The name of the service.", nargs=1)

permission_arg_parser = ArgumentParser(add_help=False)
permission_arg_parser.add_argument('permissions', metavar='PERM', nargs='*',
    help="""Add permissions to this service. If no permissions are defined, this service will not be
        able to perform any request. Possible permissions are: %s""" % perms)

host_arg_parser = ArgumentParser(add_help=False)
host_arg_parser.add_argument('hosts', metavar='HOST', nargs='*', help="""A host that the service is able to
    connect from. You can name multiple hosts as additional positional arguments. If ommitted,
    this service cannot be used from anywhere.""")
username_arg_parser = ArgumentParser(add_help=False)
username_arg_parser.add_argument('user', help="The name of the user.")

group_arg_parser = ArgumentParser(add_help=False)
group_arg_parser.add_argument('group', help="The name of the group.")
group_arg_parser.add_argument('--service', metavar="SERVICE", help="""Act as if %(prog)s was the
service named SERVICE. If ommitted, act on groups that are not associated with any service.""")

subgroup_parser = ArgumentParser(add_help=False)
subgroup_parser.add_argument('subgroup', help="The name of the subgroup.")
subgroup_parser.add_argument('--sub-service', metavar='SUBSERVICE',
    help="""Assume that the named subgroup is from SUBSERVICE.""")

###############################
### restauth-service parser ###
###############################
service_desc = """%(prog)s manages services in RestAuth. Services are websites, hosts, etc. that use
RestAuth as authentication service."""
service_parser = ArgumentParser(description=service_desc)

service_subparsers = service_parser.add_subparsers(title="Available actions", dest='action',
    description="""Use '%(prog)s action --help' for more help on each action.""")
service_subparsers.add_parser('add', help="Add a new service.",  description="Add a new service.",
    parents=[pwd_parser, service_arg_parser])
service_subparsers.add_parser('ls', help="List all services.",
    description="""List all available services.""")
service_subparsers.add_parser('rm', help="Remove a service.", parents=[service_arg_parser],
    description="""Completely remove a service. This will also remove any groups associated with
that service.""")
service_subparsers.add_parser('view', help="View details of a service.", parents=[service_arg_parser],
    description="View details of a service.")

subparser = service_subparsers.add_parser('set-hosts', parents=[service_arg_parser],
    help="Set hosts that a service can connect from, removes any previous hosts.",
    description="Set hosts that a service can connect from.")
subparser.add_argument('hosts', metavar='HOST', nargs='*',
    help='''Hosts that this service is able to connect from.
        Note: This must be an IPv4 or IPv6 address, NOT a hostname.''')
subparser = service_subparsers.add_parser('add-hosts', parents=[service_arg_parser],
    help="Add hosts that a service can connect from.",
    description="Add hosts that a service can connect from.")
subparser.add_argument('hosts', metavar='HOST', nargs='+',
    help='''Add hosts that this service is able to connect from.
        Note: This must be an IPv4 or IPv6 address, NOT a hostname.''')
subparser = service_subparsers.add_parser('rm-hosts', parents=[service_arg_parser],
    help="Remove hosts that a service can connect from.",
    description="Set hosts that a service can connect from.")
subparser.add_argument('hosts', metavar='HOST', nargs='+',
    help='''Remove hosts that this service is able to connect from.
        Note: This must be an IPv4 or IPv6 address, NOT a hostname.''')

service_subparsers.add_parser('set-password', parents=[service_arg_parser, pwd_parser],
    help="Set the password for a service.", description="Set the password for a service.")
subparser = service_subparsers.add_parser('add-permissions', parents=[service_arg_parser],
    help="Add permissions to a service.",
    description="Add permissions to a service.")
subparser.add_argument('permissions', metavar='PERM', nargs='+',
    help="Permissions to add to the specified service. Possible permissions are: %s" % perms)
subparser = service_subparsers.add_parser('rm-permissions', parents=[service_arg_parser],
    help="Remove permissions from a service.",
    description="Remove permissions from a service.")
subparser.add_argument('permissions', metavar='PERM', nargs='+',
    help="Permissions to remove from the specified service. Possible permissions are: %s" % perms)
subparser = service_subparsers.add_parser('set-permissions', parents=[service_arg_parser],
    help="Set permissions of a service, removes any previous permissions.",
    description="Set permissions of a service, removes any previous permissions.")
subparser.add_argument('permissions', metavar='PERM', nargs='*',
    help="Set the permissions of the specified service. Possible permissions are: %s" % perms)


############################
### restauth-user parser ###
############################
user_desc = """Manages users in RestAuth. Users are clients that want to authenticate with services
that use RestAuth."""
user_parser = ArgumentParser(description=user_desc)

user_subparsers = user_parser.add_subparsers(title="Available actions", dest='action',
    description="""Use '%(prog)s action --help' for more help on each action.""")
user_subparsers.add_parser('add', help="Add a new user.",
    parents=[username_arg_parser, pwd_parser],
    description="Add a new user.")
user_subparsers.add_parser('ls', help="List all users.", description="List all users.")
user_subparsers.add_parser('verify', help="Verify a users password.",
    parents=[username_arg_parser, pwd_parser],
    description="Verify the password of a user.") 
user_subparsers.add_parser('set-password', help="Set the password of a user.",
    parents=[username_arg_parser, pwd_parser],
    description="Set the password of a user.")
user_subparsers.add_parser('rm', help="Remove a user.", parents=[username_arg_parser],
    description="Remove a user.")

user_view_p = user_subparsers.add_parser('view', help="View details of a user.",
    parents=[username_arg_parser ], description="View details of a user.")
user_view_p.add_argument('--service', help="View information as SERVICE would see it.")

#############################
### restauth-group parser ###
#############################
group_desc = """%(prog)s manages groups in RestAuth. Groups can have users and groups as members, handing
down users to member groups. For a group to be visible to a service, it must be associated with it.
It is possible for a group to not be associated with any service, which is usefull for e.g. a group
containing global super-users. Valid actions are help, add, list, view, add-user, add-group, remove,
remove-user, and remove-group."""
group_parser = ArgumentParser(description=group_desc)

group_subparsers = group_parser.add_subparsers(title="Available actions", dest='action',
    description="""Use '%(prog)s action --help' for more help on each action.""")
group_subparsers.add_parser('add', help="Add a new group.", parents=[group_arg_parser],
    description="Add a new group.")
group_ls_parser = group_subparsers.add_parser('ls', help="List all groups.",
    description="List all groups.")
group_ls_parser.add_argument('--service', help="""Act as if %(prog)s was the
service named SERVICE. If ommitted, act on groups that are not associated with any service.""")
group_subparsers.add_parser('view', help="View details of a group.", parents=[group_arg_parser],
    description="View details of a group.")
group_subparsers.add_parser('add-user', parents=[group_arg_parser, username_arg_parser],
    help="Add a user to a group.", description="Add a user to a group.")
group_subparsers.add_parser('add-group', parents=[group_arg_parser, subgroup_parser],
    help="""Make a group a subgroup to another group.""",
    description="""Make a group a subgroup of another group. The subgroup will inherit all
        memberships from the parent group.""")
group_subparsers.add_parser('rm-user', parents=[group_arg_parser, username_arg_parser],
    help="Remove a user from a group.", description="Remove a user from a group.")
group_subparsers.add_parser('rm-group', parents=[group_arg_parser, subgroup_parser],
    help="""Remove a subgroup from a group.""",
    description="""Remove a subgroup from a group. The subgroup will no longer inherit all
        memberships from a parent group.""")
group_subparsers.add_parser('rm', parents=[group_arg_parser], help="Remove a group.",
    description="Remove a group.")

##############################
### restauth-import parser ###
##############################
import_desc = "Import user data from another system."
import_parser = ArgumentParser(description=import_desc)

import_parser.add_argument('--gen-passwords', action='store_true', default=False,
    help="Generate passwords where missing in input data and print them to stdout.")
import_parser.add_argument('--overwrite-passwords', action='store_true', default=False,
    help="""Overwrite passwords of already existing services or users if the input data contains
a password. (default: %(default)s)""")
import_parser.add_argument('--overwrite-properties', action='store_true', default=False,
    help="""Overwrite already existing properties of users. (default: %(default)s)""")
import_parser.add_argument('--skip-existing-users', action='store_true', default=False, help=
    """Skip users completely if they already exist. If not set, passwords and properties are
overwritten if their respective --overwrite-... argument is given.""")
import_parser.add_argument('--skip-existing-groups', action='store_true', default=False, help=
    """Skip groups completely if they already exist. If not set, users and subgroups will be
added to the list.""")
import_parser.add_argument('--using', default=None, metavar="ALIAS",
    help="Use different database alias. (UNTESTED!)")

import_parser.add_argument('file', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

########################
### helper functions ###
########################
def _metavar_formatter(action, default_metavar):
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
            return (result,) * tuple_size
    return format

def _format_args(action, default_metavar, format=True):
    OPTIONAL = '?'
    ZERO_OR_MORE = '*'
    ONE_OR_MORE = '+'
    PARSER = 'A...'
    REMAINDER = '...'
    
    get_metavar = _metavar_formatter(action, default_metavar)
    if action.nargs is None:
        if format:
            result = '*%s*' % get_metavar(1)
        else:
            result = '%s' % get_metavar(1)
    elif action.nargs == OPTIONAL:
        if format:
            result = '[*%s*]' % get_metavar(1)
        else:
            result = '[*%s*]' % get_metavar(1)
    elif action.nargs == ZERO_OR_MORE:
        if format:
            result = '[*%s* [*%s* ...]]' % get_metavar(2)
        else:
            result = '[%s [%s ...]]' % get_metavar(2)
    elif action.nargs == ONE_OR_MORE:
        if format:
            result = '*%s* [*%s* ...]' % get_metavar(2)
        else:
            result = '%s [%s ...]' % get_metavar(2)
    elif action.nargs == REMAINDER:
        result = '...'
    elif action.nargs == PARSER:
        result = '%s ...' % get_metavar(1)
    else:
        formats = ['%s' for _ in range(action.nargs)]
        result = ' '.join(formats) % get_metavar(action.nargs)
    return result

def format_action(action, format=True):
    if action.metavar:
        metavar = _format_args(action, action.metavar, format)
    else:
        metavar = _format_args(action, action.dest.upper(), format)
    
    if action.option_strings:
        strings = [ '%s %s'%(name, metavar) for name in action.option_strings ]
        return ', '.join(strings)
    else:
        return metavar

def format_man_usage(parser):
    """
    Get a man-page compatible usage string. This function and its nested functions are mostly
    directly copied from the argparse module.
    """
    opts = []
    args = []
    
    for action in parser._actions:
        if action.option_strings:
            opts.append(action)
        else:
            args.append(action)
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
    for i, action in enumerate(opts + args):
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
                
            parts.append(part)

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

def split_opts_and_args(parser, format_dict={}, skip_help=False):
    opts, args = [], []
    
    for action in parser._positionals._actions:
        if skip_help and type(action) == argparse._HelpAction:
            continue
        
        if not action.option_strings:
            args.append(action)
        else:
            opts.append(action)
        
    return opts, args

def write_parameters(parser, path, cmd):
    f = open(path, 'w')
    format_dict = { 'prog': parser.prog }
    opts, args = split_opts_and_args(parser, format_dict)
    
    if opts:
        f.write('.. program:: %s\n\n'%(cmd)) 
            
    for action in opts:
        if action.default != None:
            format_dict['default'] = action.default
        f.write('.. option:: %s\n'%(format_action(action, False)))
        f.write('   \n')
        f.write('   %s\n'%(' '.join(action.help.split())%format_dict))
        f.write('   \n')
        format_dict.pop('default', None)

def write_commands(parser, path, cmd):
    if not parser._subparsers:
        return
    
    f = open(path, 'w')
    commands = sorted(parser._subparsers._actions[1].choices)
    format_dict = { 'prog': parser.prog }
    for sub_cmd in commands:
        # TODO: cleanup mess in HTML output
        subparser = parser._subparsers._actions[1].choices[sub_cmd]
        subparser.prog = '%s %s'%(cmd, sub_cmd)
        
        # add name of command as header everywhere except on man pages
        f.write('.. only:: not man\n')
        f.write('   \n')
        f.write("   %s\n"%sub_cmd)
        f.write('   %s\n\n'%('^'*(len(sub_cmd))))
        f.write('   \n')
        
        # start writing the example:
        f.write('.. example:: ')
        f.write('**%s**%s\n'%(sub_cmd, format_man_usage(subparser)))
        f.write('   \n')
        f.write('   %s\n'%(' '.join(subparser.description.split())))
        f.write('   \n')
        
        # write options and arguments:
        opts, args = split_opts_and_args(subparser, format_dict, True)
        if opts or args:
            f.write('   .. program:: %s-%s\n\n'%(cmd, sub_cmd)) 
                
        for action in opts:
            f.write('   .. option:: %s\n'%(format_action(action, False)))
            f.write('      \n')
            f.write('      %s\n'%(' '.join(action.help.split())%format_dict))
            f.write('      \n')
            
        for arg in args:
            f.write('   .. option:: %s\n'%format_action(arg, False))
            f.write('      \n')
            f.write('      %s\n'%(' '.join(arg.help.split())))
            f.write('      \n')
        
    f.close()

def write_usage(parser, path):
    f = open(path, 'w')
    usage = parser.format_usage().replace('usage: ', '')
    f.write(usage)    
    f.close()