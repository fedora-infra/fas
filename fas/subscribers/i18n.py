# -*- coding: utf-8 -*-

from pyramid.events import (
    subscriber,
    NewRequest
    )

from fas.utils import _

# Prevent from being translated
ts = _


@subscriber(NewRequest)
def add_localizer(event):
    """ Update local on client's requests. """
    request = event.request
    localizer = request.localizer

    def auto_translate(*args, **kwargs):
        """ Translate strings on client's requests. """
        return localizer.translate(ts(*args, **kwargs))

    request.localizer = localizer
    request.translate = auto_translate