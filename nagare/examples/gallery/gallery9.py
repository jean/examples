#--
# Copyright (c) 2008-2011 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Adding significative URLs"""

from __future__ import with_statement

from sqlalchemy import Column, Unicode, BLOB, ForeignKey, Integer
from sqlalchemy.orm import relation

from nagare import presentation, component, editor, validator
from nagare.database import session, query

from gallerydeclarative import Entity
import thumb

class Photo(Entity):
    __tablename__ = 'photo_base'

    title = Column(Unicode(100), primary_key=True)
    img = Column(BLOB)
    thumbnail = Column(BLOB)
    gallery_id = Column(Integer, ForeignKey('gallery_data.name'))

    def __init__(self, title, img, thumbnail):
        self.title = title
        self.img = img
        self.thumbnail = thumbnail

@presentation.render_for(Photo)
def render(self, h, comp, *args):
    img = h.img.action(lambda h: str(self.img))
    return h.a(img).action(comp.answer)

@presentation.render_for(Photo, model='thumbnail')
def render(self, h, comp, *args):
    with h.div:
        h << h.img.action(lambda h: str(self.thumbnail))
        h << h.br
        h << h.a(self.title).action(lambda: comp.answer(self))
        h << h.i(' (%d octets)' % len(self.img))

    return h.root


class PhotoCreator(editor.Editor):
    def __init__(self):
        self.title = editor.Property(None)
        self.img = editor.Property(None)

        self.title.validate(lambda t: validator.to_string(t).not_empty().to_string())
        self.img.validate(self.validate_img)

    def validate_img(self, img):
        if isinstance(img, basestring):
            raise ValueError, 'Image not provided'
        return img.file.read()

    def commit(self, comp):
        if self.is_validated(('title', 'img')):
            comp.answer((self.title(), self.img.value))

@presentation.render_for(PhotoCreator)
def render(self, h, comp, *args):
    with h.form:
        with h.table(border=0):
            with h.tr:
                h << h.td('Title') << h.td(':') << h.td(h.input.action(self.title).error(self.title.error))

            with h.tr:
                h << h.td('Image') << h.td(':') << h.td(h.input(type='file').action(self.img).error(self.img.error))

            with h.tr:
                h << h.td() << h.td()
                with h.td:
                    h << h.input(type='submit', value='Add', id='submitbutton').action(lambda: self.commit(comp))
                    h << ' '
                    h << h.input(type='submit', value='Cancel', id='submitbutton').action(comp.answer)

    return h.root

# ---------------------------------------------------------------------------

class Gallery(Entity):
    __tablename__ = 'gallery_data'

    name = Column(Unicode(40), primary_key=True)
    photos = relation('Photo', backref='gallery')

    def __init__(self, name):
        self.name = name

    def add_photo(self, comp):
        r = comp.call(PhotoCreator())
        if r is not None:
            (title, img) = r

            photo = Photo(title, img, thumbnail=thumb.thumbnail(img))
            self.photos.append(photo)
            database.session.add(photo)

@presentation.render_for(Gallery)
def render(self, h, comp, *args):
    h.head.css('gallery', '''
    ul.photo_list {
        list-style: none;
    }

    ul.photo_list li {
        display: block;
        float: left;
        border: 1px dashed gray;
        padding: 1em;
        margin: 1em;
    }
    ''')

    with h.div:
        h << h.h1('Gallery: ', self.name)
        h << h.a('Add photo', style='float: right').action(lambda: self.add_photo(comp))
        h << h.br

        with h.ul(class_='photo_list'):
            for photo in self.photos:
                # The url for a photo is its title
                photo = component.Component(photo, url=photo.title)
                photo.on_answer(comp.call)

                h << h.li(photo.render(h, model='thumbnail'))

    return h.root

# From a URL received, set the components
@presentation.init_for(Gallery, "len(url) == 1")
def init(self, url, comp, *args):
    # The URL received is the name of the photo
    photo = query(Photo).get(url[0])
    if not photo:
        # A photo with this name doesn't exist
        raise presentation.HTTPNotFound()
    
    # Temporary change the Gallery (the ``comp``) with the photo
    component.call_wrapper(lambda: comp.call(component.Component(photo)))

# ---------------------------------------------------------------------------

app = lambda: query(Gallery).get(u'MyGallery')
