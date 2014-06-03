# -*- coding: utf-8 -*-

from pyramid.i18n import TranslationStringFactory

ts = TranslationStringFactory('fas')

def add_localizer(event):
    request = event.request
    localizer = request.localizer

    def auto_translate(*args, **kwargs):
        return localizer.translate(ts(*args, **kwargs))

    request.localizer = localizer
    request.translate = auto_translate