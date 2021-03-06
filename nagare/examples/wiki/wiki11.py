# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Basic HTTP authentication of the users added.

First, log as the editor 'john / john'.
Then try as the administrator 'admin / admin'.
"""
import re
import docutils.core

from nagare import component, presentation, var, continuation, security, wsgi

from wikidata import PageData


# ---------------------------------------------------------------------------

class Login(object):
    pass


@presentation.render_for(Login)
def render(self, h, *args):
    user = security.get_user()

    if not user:
        return h.i('not logged')

    return ('Welcome ', h.b(user.id))


# ---------------------------------------------------------------------------

wikiwords = re.compile(r'\b([A-Z]\w+[A-Z]+\w+)')


class Page(object):
    def __init__(self, title):
        self.title = title

    def edit(self, comp):
        content = comp.call(PageEditor(self))

        if content is not None:
            security.check_permissions('wiki.editor', self)
            page = PageData.get_by(pagename=self.title)
            page.data = content


@presentation.render_for(Page)
def render(self, h, comp, *args):
    page = PageData.get_by(pagename=self.title)

    content = docutils.core.publish_parts(page.data, writer_name='html')['html_body']
    content = wikiwords.sub(r'<wiki>\1</wiki>', content)
    html = h.parse_htmlstring(content, fragment=True)[0]

    for node in html.getiterator():
        if node.tag == 'wiki':
            a = h.a(node.text, href='page/' + node.text).action(comp.answer, unicode(node.text))
            node.replace(a)

    return (html, h.a('Edit this page', href='page/' + self.title).action(self.edit, comp))


@presentation.render_for(Page, model='meta')
def render(self, h, comp, *args):
    return ('Viewing ', h.b(self.title), h.br, h.br,
            'You can return to the ', h.a('FrontPage', href='page/FrontPage').action(comp.answer, u'FrontPage'))


# ---------------------------------------------------------------------------

class PageEditor(object):
    def __init__(self, page):
        self.page = page

    def answer(self, comp, text):
        comp.answer(text())


@presentation.render_for(PageEditor)
def render(self, h, comp, *args):
    content = var.Var()

    page = PageData.get_by(pagename=self.page.title)

    with h.form:
        with h.textarea(rows='10', cols='40').action(content):
            h << page.data
        h << h.br
        h << h.input(type='submit', value='Save').action(self.answer, comp, content)
        h << ' '
        h << h.input(type='submit', value='Cancel').action(comp.answer)

    return h.root


@presentation.render_for(PageEditor, model='meta')
def render(self, h, *args):
    return ('Editing ', h.b(self.page.title))


# ---------------------------------------------------------------------------

class Wiki(object):
    def __init__(self):
        self.login = component.Component(Login())
        self.content = component.Component(None)
        self.content.on_answer(self.goto)

        self.goto(u'FrontPage')

    def goto(self, title):
        page = PageData.get_by(pagename=title)
        if page is None:
            PageData(pagename=title, data=u'')

        self.content.becomes(Page(title))

    def select_a_page(self, comp):
        new_page = comp.call(model='all')
        self.goto(new_page)


@presentation.render_for(Wiki)
def render(self, h, comp, *args):
    h.head.css('main_css', '''
    .document:first-letter { font-size:2em }
    .meta { float:right; width: 10em; border: 1px dashed gray;padding: 1em; margin: 1em; }
    .login { font-size:0.75em; }
    ''')

    with h.div(class_='login'):
        h << self.login

    with h.div(class_='meta'):
        h << self.content.render(h, model='meta')

    h << self.content << h.hr

    h << 'View the ' << h.a('complete list of pages', href='all').action(self.select_a_page, comp)

    return h.root


@presentation.render_for(Wiki, model='all')
@security.permissions('wiki.admin')
def render(self, h, comp, *args):
    with h.ul:
        for page in PageData.query.order_by(PageData.pagename):
            with h.li:
                h << h.a(page.pagename, href='page/' + page.pagename).action(comp.answer, page.pagename)

    return h.root


# ---------------------------------------------------------------------------

@presentation.init_for(Wiki, "(len(url) == 2) and (url[0] == 'page')")
def init(self, url, *args):
    title = url[1]

    page = PageData.get_by(pagename=title)
    if page is None:
        raise presentation.HTTPNotFound()

    self.goto(title)


@presentation.init_for(Wiki, "len(url) and (url[0] == 'all')")
def init(self, url, comp, *args):
    continuation.Continuation(self.select_a_page, comp)


# ---------------------------------------------------------------------------

from peak.rules import when
from nagare.security import common


# We define 3 classes:
#
#  - the ``User`` class defines the attributes of the users
#  - the ``Authentication`` class defines how the users are identified /
#    authenticated
#  - the ``HardcodedRules`` class defines the mapping between the users and
#    the permissions

class User(common.User):
    pass


# We use the basic HTTP authentication to identify and authenticate the
# users
from nagare.security import basic_auth


class Authentication(basic_auth.Authentication):
    def get_password(self, username):
        # For this example, the passwords are the same than the users name
        return username

    # When a user is identified and authenticated, then create a ``User`` object
    def _create_user(self, username):
        return None if username is None else User(username)


class HardcodedRules(common.Rules):
    # A logged user wants to access an object protected by the 'wiki.editor'
    # permission
    @when(common.Rules.has_permission, "user and (perm == 'wiki.editor')")
    def _(self, user, perm, subject):
        # Grant access only to 'john' and 'admin'
        return user.id in ('john', 'admin')

    # A logged user wants to access an object protected by the 'wiki.admin'
    # permission
    @when(common.Rules.has_permission, "user and (perm == 'wiki.admin')")
    def _(self, user, perm, subject):
        # Grant access only to 'admin'
        return user.id == 'admin'


# A security manager is often a mixin of an authentication manager and
# a security rules manager
class SecurityManager(Authentication, HardcodedRules):
    pass


# ---------------------------------------------------------------------------

# We create a new WSGIApp class that has our security manager as its `security`
# attribute
class WSGIApp(wsgi.WSGIApp):
    def __init__(self, app_factory):
        super(WSGIApp, self).__init__(app_factory)
        self.security = SecurityManager(realm='My wiki')


app = WSGIApp(lambda: component.Component(Wiki()))
