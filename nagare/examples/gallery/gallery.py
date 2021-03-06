# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from nagare.examples.demo import Examples
from nagare.examples.gallery import gallery1, gallery2, gallery3, gallery4, gallery5, gallery6, gallery7

examples = (
    ('gallery1', ((gallery1.__doc__, gallery1.app),)),
    ('gallery2', ((gallery2.__doc__, gallery2.app),)),
    ('gallery3', ((gallery3.__doc__, gallery3.app),)),
    ('gallery4', ((gallery4.__doc__, gallery4.app),)),
    ('gallery5', ((gallery5.__doc__, gallery5.app),)),
    ('gallery6', ((gallery6.__doc__, gallery6.app),)),
    ('gallery7', ((gallery7.__doc__, gallery7.app),)),
)

# Url to display a module code from the GitHub repository
EXAMPLES_URL = 'https://github.com/nagareproject/examples/blob/master/nagare/examples/gallery/%s.py'


def app():
    return Examples('Gallery tutorial', EXAMPLES_URL, examples)
