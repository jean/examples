#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import with_statement

from nagare import presentation, editor
from lxml.html import clean

class Html:
    def __init__(self):
        self.content = ''

    def edit(self, comp):
        comp.becomes(HTMLEditor(self))
        comp.on_answer(comp.becomes, self)

@presentation.render_for(Html)
def default_view(self, h, comp, *args):
    with h.div:
        if self.content:
            h << h.parse_htmlstring(self.content, fragment=True)

        h << h.a('Edit HTML').action(self.edit, comp)

    return h.root


def to_valid_html(value, msg='Not a valid html fragment'):
    try:
        return clean.Cleaner().clean_html(value)
    except:
        raise ValueError(msg)


class HTMLEditor(editor.Editor):
    fields = ('content', )

    def __init__(self, target):
        super(HTMLEditor, self).__init__(target, self.fields)
        self.content.validate(to_valid_html)

    def commit(self, comp):
        if super(HTMLEditor, self).commit(self.fields):
            comp.answer()

@presentation.render_for(HTMLEditor)
def default_view(self, h, comp, *args):
    with h.form:
        h << h.label('HTML source code')
        h << h.textarea(self.content, rows=15, cols=30).action(self.content).error(self.content.error)
        h << h.input(type='submit', value='Save').action(self.commit, comp)
        h << ' '
        h << h.input(type='submit', value='Cancel').action(comp.answer)

    return h.root

# -----------------------------------------------------------------------------

hl_lines = (
    range(12, 62),
    (
        (4,),
        '<p>A <code>Html</code> widget is defined</p>'
        '<p>Its default view displays its HTML content</p>',
        range(4, 21)
    ),

    (
        (18,),
        '<p>When the <code>Edit HTML</code> link is clicked, the <code>edit</code> '
        'method is called and the <code>Html</code> component is changed, by '
        'a <code>becomes()</code>, to the <code>HTMLEditor</code> component</p>',
        [9, 18]
    ),

    (
        (39, 46),
        '<p>When the <code>Save</code> button is clicked, the <code>content</code> is changed, '
        'the editor answers so the <code>Html</code> widget is rendered back</p>',
        [10, 39, 46]
    ),

    (
        (48,),
        '<p>When the <code>Cancel</code> button is clicked, '
        'the editor answers so the <code>Html</code> widget is rendered back</p>',
        [10, 48]
    ),

    (
        (23, 35, 45),
        '<p><code>to_valid_html()</code> is a dedicated form field validator</p>'
        '<p>A validation method is associated to a Property object through its '
        '<code>validate()</code> method</p>',
        range(23, 28) + [35, 45]
    ),

    (
        (30,),
        '<p>Definition of a Nagare Editor</p>'
        '<p>Its default view is a form</p>'
        '<p><code>target</code> parameter is the edited <code>Html</code> widget</p>',
        range(30, 51)
    )
)
