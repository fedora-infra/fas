# -*- coding: utf-8 -*-


class GroupBindingRequested(object):

    def __init__(self, request, form, group):
        self.request = request
        self.form = form
        self.group = group