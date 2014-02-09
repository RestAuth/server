# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import argparse
import getpass
import re


def get_password(args):
    if not args.pwd: # pragma: no cover
        # Note: We cannot really test cli-code that reads from stdin.
        password = getpass.getpass('password: ')
        confirm = getpass.getpass('confirm: ')
        if password != confirm:
            print("Passwords do not match, please try again.")
            setattr(args, 'pwd', get_password(args))
        else:
            setattr(args, 'pwd', password)
    return args.pwd


###########################################
### helper functions for doc generation ###
###########################################
def _metavar_formatter(action, default_metavar):
    if action.metavar is not None:
        result = action.metavar
    elif action.choices is not None:  # pragma: no cover
        choice_strs = [str(choice) for choice in action.choices]
        result = '{%s}' % ','.join(choice_strs)
    else:
        result = default_metavar

    def format(tuple_size):
        if isinstance(result, tuple):  # pragma: no cover
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
    elif action.nargs == OPTIONAL:  # pragma: no cover
        if format:
            result = '[*%s*]' % get_metavar(1)
        else:
            result = '[%s]' % get_metavar(1)
    elif action.nargs == ZERO_OR_MORE:  # pragma: no cover
        if format:
            result = '[*%s* [*%s* ...]]' % get_metavar(2)
        else:
            result = '[%s [%s ...]]' % get_metavar(2)
    elif action.nargs == ONE_OR_MORE:  # pragma: no cover
        if format:
            result = '*%s* [*%s* ...]' % get_metavar(2)
        else:
            result = '%s [%s ...]' % get_metavar(2)
    elif action.nargs == REMAINDER:  # pragma: no cover
        result = '...'
    elif action.nargs == PARSER:  # pragma: no cover
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
        strings = ['%s %s' % (name, metavar) for name in action.option_strings]
        return ', '.join(strings)
    else:
        return metavar


def format_man_usage(parser):
    """
    Get a man-page compatible usage string. This function and its nested
    functions are mostly directly copied from the argparse module.
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
        except ValueError:  # pragma: no cover
            continue
        else:
            end = start + len(group._group_actions)
            if actions[start:end] == group._group_actions:  # pragma: no branch
                for action in group._group_actions:
                    group_actions.add(action)
                if not group.required:  # pragma: no branch
                    inserts[start] = '['
                    inserts[end] = ']'
                else:  # pragma: no cover
                    inserts[start] = '('
                    inserts[end] = ')'
                for i in range(start + 1, end):
                    inserts[i] = '|'

    parts = []
    for i, action in enumerate(opts + args):
        if action.help is argparse.SUPPRESS:  # pragma: no cover
            parts.append(None)
            if inserts.get(i) == '|':
                inserts.pop(i)
            elif inserts.get(i + 1) == '|':
                inserts.pop(i + 1)
        elif not action.option_strings:  # args
            part = _format_args(action, action.dest)

            # if it's in a group, strip the outer []
            if action in group_actions:  # pragma: no cover
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

    return ' %s' % text


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


def write_parameters(f, parser, cmd):
    format_dict = {'prog': parser.prog}
    opts, args = split_opts_and_args(parser, format_dict)

    if opts:  # pragma: no branch
        f.write('.. program:: %s\n\n' % (cmd))

    for action in opts:
        if action.default is not None:  # pragma: no branch
            format_dict['default'] = action.default
        f.write('.. option:: %s\n' % (format_action(action, False)))
        f.write('   \n')
        f.write('   %s\n' % (' '.join(action.help.split()) % format_dict))
        f.write('   \n')
        format_dict.pop('default', None)


def write_commands(f, parser, cmd):
    if not parser._subparsers:  # pragma: no cover
        return

    commands = sorted(parser._subparsers._actions[1].choices)
    format_dict = {'prog': parser.prog}
    for sub_cmd in commands:
        # TODO: cleanup mess in HTML output
        subparser = parser._subparsers._actions[1].choices[sub_cmd]
        subparser.prog = '%s %s' % (cmd, sub_cmd)

        # add name of command as header everywhere except on man pages
        f.write('.. only:: not man\n')
        f.write('   \n')
        f.write("   %s\n" % sub_cmd)
        f.write('   %s\n\n' % ('^' * (len(sub_cmd))))
        f.write('   \n')

        # start writing the example:
        f.write('.. example:: ')
        f.write('**%s**%s\n' % (sub_cmd, format_man_usage(subparser)))
        f.write('   \n')
        f.write('   %s\n' % (' '.join(subparser.description.split())))
        f.write('   \n')

        # write options and arguments:
        opts, args = split_opts_and_args(subparser, format_dict, True)
        if opts or args:
            f.write('   .. program:: %s-%s\n\n' % (cmd, sub_cmd))

        for action in opts:
            help = ' '.join(action.help.split()) % format_dict
            f.write('   .. option:: %s\n' % (format_action(action, False)))
            f.write('      \n')
            f.write('      %s\n' % (help))
            f.write('      \n')

        for arg in args:
            f.write('   .. option:: %s\n' % format_action(arg, False))
            f.write('      \n')
            f.write('      %s\n' % (' '.join(arg.help.split())))
            f.write('      \n')


def write_usage(f, parser, cmd=None):
    usage = parser.format_usage().replace('usage: ', '')
    usage = usage.replace("\n", '')
    usage = re.sub('\s{2,}', ' ', usage)
    f.write('.. parsed-literal:: %s' % usage)
