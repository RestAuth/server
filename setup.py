# -*- coding: utf-8 -*-
#
# This file is part of RestAuth (https://restauth.net).
#
# RestAuth is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# RestAuth is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with RestAuth. If not, see
# <http://www.gnu.org/licenses/>.

import os
import shutil
import subprocess
import sys
from distutils.command.clean import clean as _clean
from subprocess import Popen

from setuptools import Command
from setuptools import find_packages
from setuptools import setup
from setuptools.command.install_scripts import install_scripts as _install_scripts

requires = [
    'Django>=1.8',
    'RestAuthCommon>=0.7.0',
    'python-mimeparse>=1.6.0',
    'django-hashers-passlib>=0.3',
]
_rootdir = os.path.dirname(os.path.realpath(__file__))

# Setup environment
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.settings'

common_path = os.path.join('..', 'RestAuthCommon', 'python')
if os.path.exists(common_path):
    sys.path.insert(0, common_path)
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        os.environ['PYTHONPATH'] += ':%s' % common_path
    else:
        os.environ['PYTHONPATH'] = common_path

LATEST_RELEASE = '0.6.4'

if os.path.exists('RestAuth'):
    sys.path.insert(0, 'RestAuth')


class install_scripts(_install_scripts):
    def run(self):
        _install_scripts.run(self)

        # rename manage.py to restauth-manage.py
        source = os.path.join(self.install_dir, 'manage.py')
        target = os.path.join(self.install_dir, 'restauth-manage.py')
        os.rename(source, target)


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
    description = "Output version of this software."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print(LATEST_RELEASE)


class build_doc_meta(Command):
    user_options = [
        ('target=', 't', 'What distribution to build for'),
    ]

    def __init__(self, *args, **kwargs):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'

        Command.__init__(self, *args, **kwargs)

        # import here so coverage results are not tainted:
        from Users.models import user_permissions
        from Users.models import prop_permissions
        from Groups.models import group_permissions
        from common.cli import helpers
        from Services.cli import parsers as service_parser
        from Users.cli import parsers as user_parser
        from Groups.cli import parsers as group_parser
        from common.cli import parsers as import_parser

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

                    with open(filename, 'w') as f:
                        func(f, parser.parser, name)

        # generate permissions:
        self.write_perm_table('users', user_permissions)
        self.write_perm_table('properties', prop_permissions)
        self.write_perm_table('groups', group_permissions)

        pythonpath = os.environ.get('PYTHONPATH')
        if pythonpath:
            os.environ['PYTHONPATH'] += ':.'
        else:
            os.environ['PYTHONPATH'] = '.'
        common_path = os.path.abspath(os.path.join('..', 'RestAuthCommon', 'python'))
        if os.path.exists(common_path):
            os.environ['PYTHONPATH'] += ':%s' % common_path

        os.environ['SPHINXOPTS'] = '-D release=%s -D version=%s' \
            % (LATEST_RELEASE, LATEST_RELEASE)
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
        import django
        django.setup()

        from django.core.management import call_command

        if self.app:
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

        os.environ['DJANGO_SETTINGS_MODULE'] = 'RestAuth.testsettings'
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        omit = [
            '*testdata.py',
            '*settings.py',
            '*migrations/*.py',
            'RestAuth/common/decorators.py',
            'RestAuth/common/profile.py',
            'RestAuth/common/routers.py',
            'RestAuth/manage.py',
            'RestAuth/RestAuth/wsgi.py',
            'RestAuth/*/tests.py',
        ]

        import django
        django.setup()
        from django.conf import settings
        from django.core.management import call_command
        from django.utils import six

        # compute backend files to exclude:
        backend_path = 'RestAuth/backends/'
        backend_whitelist = ['__init__.py', 'base.py']
        mod = settings.DATA_BACKEND['BACKEND'].rsplit('.', 2)[2]
        backend_mods = [os.path.splitext(f)[0] for f in os.listdir(backend_path)
                        if f.endswith('py') and f not in backend_whitelist and f != '%s.py' % mod]
        for backend_mod in backend_mods:
            omit.append('%s%s.py' % (backend_path, backend_mod))

        cov = coverage.coverage(cover_pylib=False, source=['RestAuth', ],
                                branch=True, omit=omit)

        # exclude some patterns:
        cov.exclude('\t*self.fail\(.*\)')
        if not settings.SECURE_CACHE:
            cov.exclude('\t*if settings.SECURE_CACHE:')

        if six.PY3:
            cov.exclude('pragma: py2')  # exclude py2 code
        else:
            cov.exclude('pragma: py3')  # exclude py3 code

        cov.start()

        call_command('test', 'Users', 'Groups', 'Test', 'Services', 'common')

        cov.stop()
        cov.save()
        cov.html_report(directory=self.dir)
#        cov.report()


class QualityCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RestAuth.testsettings")

        print('isort --check-only --diff -rc ca/ fabfile.py setup.py')
        status = subprocess.call(['isort', '--check-only', '--diff', '-rc', 'RestAuth', 'setup.py'])
        if status != 0:
            sys.exit(status)

        print('flake8 RestAuth/ setup.py')
        status = subprocess.call(['flake8', 'RestAuth/', 'setup.py'])
        if status != 0:
            sys.exit(status)

        work_dir = os.path.join(_rootdir, 'RestAuth')

        os.chdir(work_dir)
        print('python -Wd manage.py check')
        status = subprocess.call(['python', '-Wd', 'manage.py', 'check'], env={
            'DJANGO_SETTINGS_MODULE': os.environ['DJANGO_SETTINGS_MODULE'],
        })
        if status != 0:
            sys.exit(status)


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
            management.call_command('loaddata', fixture)

            use_threading = conn.features.test_db_allows_multiple_connections
            management.call_command(
                'runserver',
                shutdown_message='Testserver stopped.',
                use_reloader=False,
                use_ipv6=True,
                use_threading=use_threading
            )
        else:
            management.call_command('testserver', fixture, use_ipv6=True)


setup(
    name='RestAuth',
    version=str(LATEST_RELEASE),
    description='RestAuth server',
    author='Mathias Ertl',
    author_email='mati@restauth.net',
    url='https://restauth.net',
    download_url='https://server.restauth.net/download',
    install_requires=requires,
    license="GNU General Public License (GPL) v3",
    packages=find_packages(exclude=['RestAuth.bin', ]),
    scripts=[
        'RestAuth/bin/restauth-service.py', 'RestAuth/bin/restauth-user.py',
        'RestAuth/bin/restauth-group.py', 'RestAuth/bin/restauth-import.py',
        'RestAuth/manage.py',
    ],
    # NOTE: The RestAuth/ prefix for data_files is the location that all files get installed to if
    #       installed via pip. Make sure files are included in the package via MANIFEST.in.
    data_files=[
        ('RestAuth/munin', ['munin/%s' % f for f in os.listdir('munin')]),
        ('RestAuth/uwsgi', ['doc/files/uwsgi.ini', ]),
        ('RestAuth/doc', ['AUTHORS', 'COPYING', 'COPYRIGHT', ]),
        ('RestAuth/config', [
            'RestAuth/RestAuth/localsettings.py.example',
            'RestAuth/RestAuth/__init__.py',
        ])
    ],
    cmdclass={
        'build_doc': build_doc,
        'build_html': build_html,
        'build_man': build_man,
        'clean': clean,
        'coverage': coverage,
        'install_scripts': install_scripts,
        'test': test,
        'testserver': testserver,
        'version': version,
        'code_quality': QualityCommand,
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration :: Authentication/Directory",
    ],
    long_description="""RestAuth is the server-side reference implementation of
the `RestAuth protocol <https://restauth.net/Specification>`_. Please see
`server.restauth.net <https://server.restauth.net>`_ for extensive
documentation."""
)
