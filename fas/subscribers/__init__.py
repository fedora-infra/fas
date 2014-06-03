# -*- coding: utf-8 -*-

def add_renderer_globals(event):
    request = event['request']

    event['_'] = request.translate
    event['localizer'] = request.localizer

