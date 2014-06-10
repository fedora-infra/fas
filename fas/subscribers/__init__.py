# -*- coding: utf-8 -*-

from pyramid.events import (
    subscriber,
    BeforeRender
    )


@subscriber(BeforeRender)
def add_renderer_globals(event):
    request = event['request']

    event['_'] = request.translate
    event['localizer'] = request.localizer

