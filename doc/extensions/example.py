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

from docutils import nodes
from sphinx.util.compat import Directive
from sphinx.util.compat import make_admonition

from sphinx.locale import _

class ExampleDirective(Directive):

    # this enables content in the directive
    has_content = True

    def run(self):
        env = self.state.document.settings.env

        targetid = "example-%d" % env.new_serialno('example')
        targetnode = nodes.target('', '', ids=[targetid])
        
        ad = make_admonition(example, self.name, [], self.options,
                             self.content, self.lineno, self.content_offset,
                             self.block_text, self.state, self.state_machine)

        return [targetnode] + ad

class example(nodes.Admonition, nodes.Element):
    pass

def node_to_man( self, node ):
    if node.tagname == 'strong':
        return '\\fB%s\\fP'%node.astext()
    elif node.tagname == 'emphasis':
        return '\\fI%s\\fP'%node.astext()
    else:
        return node.astext()

def visit_man_node(self, node):
    self.body.append( '.sp\n' )
    header = node.pop(0)
    for child in header.children:
        self.body.append( node_to_man( self, child ) )
    self.body.append( '\n.INDENT 0.0\n')
    section_name = node.parent.children[0].astext()
    
#    if section_name == 'Examples':
    self.body.append( '.INDENT 7\n')

def depart_man_node(self, node):
    self.body.append( '.UNINDENT\n')
    section_name = node.parent.children[0].astext()
    
#    if section_name == 'Examples':
    self.body.append( '.UNINDENT\n')
    

def visit_html_node(self, node):
    self.body.append(self.starttag(node, 'dl'))
    header = node.pop(0)
    for child in header.children:
        if child.tagname   == 'emphasis':
            child.tagname = 'em'
    self.body.append( '<dt>%s</dt><dd>'%header)

def depart_html_node(self, node):
    self.body.append( '</dd></dl>')

def setup(app):
    app.add_node(example,
                 html=(visit_html_node, depart_html_node),
                 man=(visit_man_node, depart_man_node) )

    app.add_directive('example', ExampleDirective)