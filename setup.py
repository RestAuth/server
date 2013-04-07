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

import os
import re
import shutil
import sys

from subprocess import Popen
from subprocess import PIPE

from distutils.command.clean import clean as _clean
from distutils.command.install_data import install_data as _install_data

try:
    from setuptools import Command
    from setuptools import setup
    from setuptools.command.install import install as _install
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import Command
    from setuptools import setup
    from setuptools.command.install import install as _install

requires = ['RestAuthCommon>=0.6.1', 'mimeparse>=0.1.3', ]

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

common_path = os.path.join('..', 'restauth-common', 'python')
if os.path.exists(common_path):
    sys.path.insert(0, common_path)
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        os.environ['PYTHONPATH'] += ':%s' % common_path
    else:
        os.environ['PYTHONPATH'] = common_path

from django.conf import settings
from django.core.management import call_command

LATEST_RELEASE = '0.6.0'

if os.path.exists('RestAuth'):
    sys.path.insert(0, 'RestAuth')


def get_version():
    """
    Dynamically get the current version.
    """
    version = LATEST_RELEASE  # default
    if os.path.exists('.version'):  # get from file
        version = open('.version').readlines()[0]
    elif os.path.exists('.git'):  # get from git
        cmd = ['git', 'describe', 'master']
        p = Popen(cmd, stdout=PIPE)
        version = p.communicate()[0].decode('utf-8')
    elif os.path.exists('debian/changelog'):  # building .deb
        f = open('debian/changelog')
        version = re.search('\((.*)\)', f.readline()).group(1)
        f.close()

        if ':' in version:  # strip epoch:
            version = version.split(':', 1)[1]
        version = version.rsplit('-', 1)[0]  # strip debian revision
    return version.strip()


class install_data(_install_data):
    """
    Improve the install_data command so it can also copy directories
    """
    def custom_copy_tree(self, src, dest):
        base = os.path.basename(src)
        dest = os.path.normpath("%s/%s/%s" % (self.install_dir, dest, base))
        if os.path.exists(dest):
            return
        ignore = shutil.ignore_patterns('.svn', '*.pyc')
        print("copying %s -> %s" % (src, dest))
        shutil.copytree(src, dest, ignore=ignore)

    def run(self):
        for dest, nodes in self.data_files:
            dirs = [node for node in nodes if os.path.isdir(node)]
            for src in dirs:
                self.custom_copy_tree(src, dest)
                nodes.remove(src)
        _install_data.run(self)


class install(_install):
    def run(self):
        _install.run(self)

        # write symlink for restauth-manage.py
        source = os.path.join(self.install_scripts, 'manage.py')
        target = os.path.join(self.install_scripts, 'restauth-manage.py')

        os.rename(source, target)
#        # set execute permissions:
#        mode = os.stat(source).st_mode
#        os.chmod(source, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

added_options = [
    ('prefix=', None, 'installation prefix'),
    ('exec-prefix=', None, 'prefix for platform-specific files')
]


class clean(_clean):
    def initialize_options(self):
        _clean.initialize_options(self)

    def run(self):
        _clean.run(self)

        # clean sphinx documentation:
        cmd = ['make', '-C', 'doc', 'clean']
        p = Popen(cmd)
        p.communicate()

        coverage = os.path.join('doc', 'coverage')
        generated = os.path.join('doc', 'gen')

        if os.path.exists(coverage):
            print('rm -r %s' % coverage)
            shutil.rmtree(os.path.join('doc', 'coverage'))
        if os.path.exists(generated):
            print('rm -r %s' % generated)
            shutil.rmtree(generated)
        if os.path.exists('MANIFEST'):
            print('rm MANIFEST')
            os.remove('MANIFEST')


class version(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print(get_version())


class build_doc_meta(Command):
    user_options = [
        ('target=', 't', 'What distribution to build for'),
    ]

    def __init__(self, *args, **kwargs):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        Command.__init__(self, *args, **kwargs)

        # import here so coverage results are not tainted:
        from RestAuth.Users.models import user_permissions, prop_permissions
        from RestAuth.Groups.models import group_permissions
        from RestAuth.common.cli import helpers
        from RestAuth.Services.cli import parsers as service_parser
        from RestAuth.Users.cli import parsers as user_parser
        from RestAuth.Groups.cli import parsers as group_parser
        from RestAuth.common.cli import parsers as import_parser

        # generate files for cli-scripts:
        service_parser.parser.prog = '|bin-restauth-service|'
        user_parser.parser.prog = '|bin-restauth-user|'
        group_parser.parser.prog = '|bin-restauth-group|'
        import_parser.parser.prog = '|bin-restauth-import|'

        # create necesarry folders:
        if not os.path.exists('doc/_static'):
            os.mkdir('doc/_static')
        if not os.path.exists('doc/gen'):
            os.mkdir('doc/gen')

        for parser, name in [(service_parser, 'restauth-service'),
                             (user_parser, 'restauth-user'),
                             (group_parser, 'restauth-group'),
                             (import_parser, 'restauth-import')]:

            for suffix in ['usage', 'commands', 'parameters']:
                filename = 'doc/gen/%s-%s.rst' % (name, suffix)
                if self.should_generate(parser.__file__, filename):
                    func = getattr(helpers, 'write_%s' % suffix)
                    func(parser.parser, filename, name)

        # generate permissions:
        self.write_perm_table('users', user_permissions)
        self.write_perm_table('properties', prop_permissions)
        self.write_perm_table('groups', group_permissions)

        pythonpath = os.environ.get('PYTHONPATH')
        if pythonpath:
            os.environ['PYTHONPATH'] += ':.'
        else:
            os.environ['PYTHONPATH'] = '.'
        common_path = os.path.abspath(
            os.path.join('..', 'restauth-common', 'python'))
        if os.path.exists(common_path):
            os.environ['PYTHONPATH'] += ':%s' % common_path

        version = get_version()
        os.environ['SPHINXOPTS'] = '-D release=%s -D version=%s' \
            % (version, version)
        os.environ['RESTAUTH_LATEST_RELEASE'] = LATEST_RELEASE

    def write_perm_table(self, suffix, perms):
        f = open('doc/gen/restauth-service-permissions-%s.rst' % suffix, 'w')

        col_1_header = 'permission'
        col_2_header = 'description'

        col_1_length = max([len(x) for x, y in perms] + [len(col_1_header)])
        col_2_length = max([len(y) for x, y in perms] + [len(col_2_header)])
        f.write('%s %s\n' % ('=' * col_1_length, '=' * col_2_length))
        f.write('%s ' % col_1_header.ljust(col_1_length, ' '))
        f.write('%s\n' % col_2_header.ljust(col_2_length, ' '))
        f.write('%s %s\n' % ('=' * col_1_length, '=' * col_2_length))

        for codename, name in perms:
            f.write('%s ' % codename.ljust(col_1_length, ' '))
            f.write('%s\n' % name.ljust(col_2_length, ' '))

        f.write('%s %s\n' % ('=' * col_1_length, '=' * col_2_length))

        f.close()

    def should_generate(self, source, generated):
        if not os.path.exists(os.path.dirname(generated)):
            os.mkdirs(os.path.dirname(generated))
            return True
        if not os.path.exists(generated):
            return True
        if os.stat(source).st_mtime > os.stat(generated).st_mtime:
            return True
        return False

    def initialize_options(self):
        self.target = None

    def finalize_options(self):
        if self.target:
            os.environ['SPHINXOPTS'] += ' -t %s' % self.target
        else:
            os.environ['SPHINXOPTS'] += ' -t source'


class build_doc(build_doc_meta):
    description = "Build documentation as HTML and man-pages"

    def run(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        cmd = ['make', '-C', 'doc', 'man', 'html']
        p = Popen(cmd)
        p.communicate()


class build_html(build_doc_meta):
    description = "Build HTML documentation"

    def run(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        cmd = ['make', '-C', 'doc', 'html']
        p = Popen(cmd)
        p.communicate()


class build_man(build_doc_meta):
    description = "Build man-pages"

    def run(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        cmd = ['make', '-C', 'doc', 'man']
        p = Popen(cmd)
        p.communicate()


class test(Command):
    user_options = [
        ('app=', None, 'Only test the specified app'),
    ]

    def initialize_options(self):
        self.app = None

    def finalize_options(self):
        pass

    def run(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        if self.app:
            print(self.app)
            call_command('test', self.app)
        else:
            call_command('test', 'Users', 'Groups', 'Test', 'Services',
                         'common',)


class coverage(Command):
    description = "Run test suite and generate code coverage analysis."
    user_options = [
        ('output-dir=', 'o', 'Output directory for coverage analysis'),
    ]

    def initialize_options(self):
        self.dir = 'doc/coverage'

    def finalize_options(self):
        pass

    def run(self):
        try:
            import coverage
        except ImportError:
            print("You need coverage.py installed.")
            return

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        omit = [
            '*testdata.py',
            '*settings.py',
            '*migrations/*.py',
            'RestAuth/*/cli/*',
            'RestAuth/common/decorators.py',
            'RestAuth/common/profile.py',
            'RestAuth/common/routers.py',
        ]

        # compute backend files to exclude:
        backend_path = 'RestAuth/backends/'
        backend_whitelist = ['__init__.py', 'base.py']
        backend_mods = [os.path.splitext(f)[0]
                        for f in os.listdir(backend_path)
                        if f.endswith('py') and f not in backend_whitelist]
        used_backend_mods = [mod.rsplit('.', 2)[1] for mod in [
            settings.USER_BACKEND, settings.GROUP_BACKEND,
            settings.PROPERTY_BACKEND
        ]]
        for mod in backend_mods:
            if mod not in used_backend_mods:
                omit.append('%s%s.py' % (backend_path, mod))

        cov = coverage.coverage(cover_pylib=False, source=['RestAuth', ],
                                branch=True, omit=omit)

        # exclude some patterns:
        cov.exclude('\t*self.fail\(.*\)')
        if not settings.SECURE_CACHE:
            cov.exclude('\t*if settings.SECURE_CACHE:')

        cov.start()

        call_command('test', 'Users', 'Groups', 'Test', 'Services', 'common')

        cov.stop()
        cov.save()
        cov.html_report(directory=self.dir)
#        cov.report()


class testserver(Command):
    description = "Run a testserver on http://[::1]:8000"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        import django
        from django.core import management

        # this causes django to use stock syncdb instead of South-version
        management.get_commands()
        management._commands['syncdb'] = 'django.core'

        fixture = 'RestAuth/fixtures/testserver.json'
        if django.VERSION[:2] == (1, 4):
            # see https://github.com/django/django/commit/bb4452f212e211bca7b6b57904d59270ffd7a503
            from django.db import connection as conn

            # Create a test database.
            conn.creation.create_test_db()

            # Import the fixture data into the test database.
            call_command('loaddata', fixture)

            use_threading = conn.features.test_db_allows_multiple_connections
            call_command(
                'runserver',
                shutdown_message='Testserver stopped.',
                use_reloader=False,
                use_ipv6=True,
                use_threading=use_threading
            )
        else:
            call_command('testserver', fixture, use_ipv6=True)


class prepare_debian_changelog(Command):
    description = "prepare debian/changelog file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not os.path.exists('debian/changelog'):
            sys.exit(0)

        version = get_version()
        cmd = ['sed', '-i', '1s/(.*)/(%s-1)/' % version, 'debian/changelog']
        p = Popen(cmd)
        p.communicate()

setup(
    name='RestAuth',
    version=str(get_version()),
    description='RestAuth server',
    author='Mathias Ertl',
    author_email='mati@restauth.net',
    url='https://restauth.net',
    download_url='https://server.restauth.net/download',
    install_requires=requires,
    license="GNU General Public License (GPL) v3",
    packages=[
        'RestAuth',
        'RestAuth.Groups',
        'RestAuth.Groups.cli',
        'RestAuth.Groups.migrations',
        'RestAuth.Services',
        'RestAuth.Services.cli',
        'RestAuth.Services.migrations',
        'RestAuth.Test',
        'RestAuth.Users',
        'RestAuth.Users.cli',
        'RestAuth.Users.migrations',
        'RestAuth.backends',
        'RestAuth.common',
        'RestAuth.common.cli',
    ],
    scripts=[
        'RestAuth/bin/restauth-service.py', 'RestAuth/bin/restauth-user.py',
        'RestAuth/bin/restauth-group.py', 'RestAuth/bin/restauth-import.py',
        'manage.py',
    ],
    data_files=[
        ('share/restauth', ['wsgi', 'RestAuth/fixtures', 'munin', ]),
        ('share/restauth/uwsgi', ['doc/files/uwsgi.ini', ]),
        ('share/doc/restauth', ['AUTHORS', 'COPYING', 'COPYRIGHT', ]),
    ],
    cmdclass={
        'clean': clean,
        'build_doc': build_doc, 'build_man': build_man,
        'build_html': build_html,
        'install': install, 'install_data': install_data,
        'version': version,
        'test': test, 'coverage': coverage, 'testserver': testserver,
        'prepare_debian_changelog': prepare_debian_changelog,
    },
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Other Environment",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration :: Authentication/Directory",
    ],
    long_description="""RestAuth is the server-side reference implementation of
the `RestAuth protocol <https://restauth.net/Specification>`_. Please see
`server.restauth.net <https://server.restauth.net>`_ for extensive
documentation.

This project requires `RestAuthCommon <https://common.restauth.net>`_
(`PyPI <https://pypi.python.org/pypi/RestAuthCommon/>`_) and
`mimeparse <http://code.google.com/p/mimeparse/>`_
(`PyPI <https://pypi.python.org/pypi/mimeparse/>`_).
"""
)
