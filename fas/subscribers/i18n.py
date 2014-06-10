# -*- coding: utf-8 -*-

from pyramid.events import (
    subscriber,
    NewRequest
    )

from pyramid.i18n import TranslationStringFactory

ts = TranslationStringFactory('fas')


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