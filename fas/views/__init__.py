# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPFound


def redirect_to(url):
    """ Reroute to given url.

    :arg url: String, url to be redirected to.
    """
    return HTTPFound(location=url)