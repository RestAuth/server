# -*- coding: utf-8 -*-
#
# RestAuth documentation build configuration file, created by
# sphinx-quickstart on Sun Jul  3 12:18:18 2011.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
import sys

sys.path.insert(0, '..')
sys.path.insert(0, '../RestAuth')
sys.path.insert(0, 'RestAuth')

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.coverage',
    'sphinx.ext.ifconfig', 'sphinx.ext.viewcode',
    'sphinx.ext.extlinks',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'RestAuth'
copyright = u'2010-2012, Mathias Ertl'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.6.4'
# The full version, including alpha/beta/rc tags.
release = '0.6.4'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'includes', 'gen', ]

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'RestAuthdoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ('index', 'RestAuth.tex', u'RestAuth Documentation', u'Mathias Ertl', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('restauth-service', 'restauth-service', u'manage services that use RestAuth',
     [u'Mathias Ertl'], 1),
    ('restauth-user', 'restauth-user', u'manage users in RestAuth',
     [u'Mathias Ertl'], 1),
    ('restauth-group', 'restauth-group', u'manage groups in RestAuth',
     [u'Mathias Ertl'], 1),
    ('restauth-import', 'restauth-import', u'import data into RestAuth',
     [u'Mathias Ertl'], 1),
    ('bin/restauth-manage', 'restauth-manage', u'advanced RestAuth management',
     [u'Mathias Ertl'], 1),
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/': None}

# default substitutions, generally, this should reflect the installation from source.
defaults = {
    'bin-restauth-manage': 'restauth-manage.py',
    'bin-restauth-service': 'restauth-service.py',
    'bin-restauth-user': 'restauth-user.py',
    'bin-restauth-group': 'restauth-group.py',
    'bin-restauth-import': 'restauth-import.py',

    'file-settings': 'RestAuth/localsettings.py',
    'file-wsgi': 'RestAuth/RestAuth/wsgi.py',
}

settings = {
    'homepage': {
        'bin-restauth-manage': 'restauth-manage',
        'bin-restauth-service': 'restauth-service',
        'bin-restauth-user': 'restauth-user',
        'bin-restauth-group': 'restauth-group',
        'bin-restauth-import': 'restauth-import',

        'file-settings': 'localsettings.py',
        'file-wsgi': '/path/to/your/wsgi.py',
    },
    'debian': {
        'bin-restauth-manage': 'restauth-manage',
        'bin-restauth-service': 'restauth-service',
        'bin-restauth-user': 'restauth-user',
        'bin-restauth-group': 'restauth-group',
        'bin-restauth-import': 'restauth-import',

        'file-settings': '/etc/restauth/settings.py',
        'file-wsgi': '/usr/share/pyshared/RestAuth/RestAuth/wsgi.py',
    },
    'man': {
    },
    'fedora': {
    },
    'arch': {
        'file-wsgi': '/usr/share/restauth/wsgi.py',
    },
}

substitutions = defaults

# set the -default suffix:
for key, value in list(defaults.items()):
    substitutions['%s-default' % key] = value

# apply tags (should be only one, really):
for dist, dist_settings in list(settings.items()):
    for key, value in dist_settings.items():
        substitutions['%s-%s' % (key, dist)] = value

        # update default if -t <dist> is given
        if tags.has(dist):
            substitutions[key] = value

substitutions.update({
    'restauth-import-format': ':doc:`import format </migrate/import-format>`',
    'restauth-import': ':doc:`restauth-import </restauth-import>`',
    'restauth-latest-release': os.environ.get('RESTAUTH_LATEST_RELEASE', version),
})

if tags.has('man'):
    substitutions['restauth-import-format'] = ':manpage:`restauth-import(5)`'
    substitutions['restauth-import'] = ':manpage:`restauth-import(1)`'

rst_epilog = ""

if tags.has('homepage'):
    rst_epilog += """
.. |bin-restauth-manage-link| replace:: :ref:`%s <dist-specific-bin-restauth-manage>`
.. |bin-restauth-service-link| replace:: :ref:`%s <dist-specific-bin-restauth-service>`
.. |bin-restauth-user-link| replace:: :ref:`%s <dist-specific-bin-restauth-user>`
.. |file-settings-link| replace:: :ref:`%s <dist-specific-file-settings>`
""" % (
        settings['homepage']['bin-restauth-manage'],
        settings['homepage']['bin-restauth-service'],
        settings['homepage']['bin-restauth-user'],
        settings['homepage']['file-settings'],
    )
else:
    rst_epilog += """
.. |bin-restauth-manage-link| replace:: :doc:`%s </bin/restauth-manage>`
.. |bin-restauth-service-link| replace:: :doc:`%s </restauth-service>`
.. |bin-restauth-user-link| replace:: :doc:`%s </restauth-user>`
.. |file-settings-link| replace:: :doc:`%s </config/all-config-values>`
""" % (
        substitutions['bin-restauth-manage'],
        substitutions['bin-restauth-service'],
        substitutions['bin-restauth-user'],
        substitutions['file-settings'],
    )

for key, value in substitutions.items():
    rst_epilog += ".. |%s| replace:: %s\n" % (key, value)

    if key.startswith('bin-') or key.startswith('file-'):
        rst_epilog += ".. |%s-bold| replace:: **%s**\n" % (key, value)

    if key.startswith('bin-'):
        rst_epilog += ".. |%s-as-cmd| replace:: :command:`%s`\n" % (key, value)
    if key.startswith('file-'):
        rst_epilog += ".. |%s-as-file| replace:: :file:`%s`\n" % (key, value)

if tags.has('homepage'):
    dist_conf_targets = {
        'file-settings':
            '/config/all-config-values.html#dist-specific-file-settings',
        'bin-restauth-manage':
            '/bin/restauth-manage.html#dist-specific-bin-restauth-manage',
        'bin-restauth-service':
            '/restauth-service.html#dist-specific-bin-restauth-service',
        'bin-restauth-user':
            '/restauth-user.html#dist-specific-bin-restauth-user',
        'bin-restauth-group':
            '/restauth-group.html#dist-specific-bin-restauth-group',
        'bin-restauth-import':
            '/restauth-import.html#dist-specific-bin-restauth-import',
    }

#    for key, value in dist_conf_targets.items():
#        rst_epilog += ".. _%s-link-hp: %s\n" % (key, value)

# links to binary documents:
rst_epilog += ".. |bin-restauth-manage-doc| replace:: :doc:`/bin/restauth-manage`\n"
rst_epilog += ".. |bin-restauth-service-doc| replace:: :doc:`/restauth-service`\n"
rst_epilog += ".. |bin-restauth-user-doc| replace:: :doc:`/restauth-user`\n"
rst_epilog += ".. |bin-restauth-group-doc| replace:: :doc:`/restauth-group`\n"
rst_epilog += ".. |bin-restauth-import-doc| replace:: :doc:`/restauth-import`\n"
rst_epilog += ".. _DATABASES: https://docs.djangoproject.com/en/dev/ref/databases/\n"

LINKS = {
    # restauth links:
    'chat': 'xmpp:rest@conference.jabber.at',
    'git': 'https://github.com/RestAuth/server.git',
    'git-web': 'https://github.com/RestAuth/server',
    'issue-tracker': 'https://github.com/RestAuth/server/issues',
    'issue-tracker-new': 'https://github.com/RestAuth/server/issues/new',
    'download-releases': 'https://server.restauth.net/download',

    # other RestAuth projects
    'RestAuthCommon': 'https://common.restauth.net',

    # external projects:
    'Django South': 'http://south.aeracode.org',
    'Django': 'https://www.djangoproject.com',
    'PyPI': 'http://pypi.python.org/',
    'Python': 'http://www.python.org',
    'argparse': 'http://docs.python.org/library/argparse.html',
}

for key, url in LINKS.items():
    rst_epilog += ".. _%s: %s\n" % (key, url)
    rst_epilog += ".. |%s| replace:: %s\n" % (key, url)

# external links:
extlinks = {
    'pypi': ('https://pypi.python.org/pypi/%s', ''),
}
