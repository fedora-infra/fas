# -*- coding: utf-8 -*-

import hashlib


def gen_libravatar(id):
    """ Get libravatar's URL based on given id. """
    base_url = 'http://cdn.libravatar.org/avatar/'

    return base_url + hashlib.md5(id.strip().lower()).hexdigest()