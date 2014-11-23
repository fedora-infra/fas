# -*- coding: utf-8 -*-


class GroupBindingRequested(object):
    """ Group binding request event. """
    def __init__(self, request, form, group):
        self.request = request
        self.form = form
        self.group = group


class LoginRequested(object):
    """ Login success event. """
    def __init__(self, request, person):
        self.request = request
        self.person = person


class LoginSucceeded(object):
    """ Login success event. """
    def __init__(self, request, person):
        self.request = request
        self.person = person


class LoginFailed(object):
    """ Login failure event. """
    def __init__(self, request, person):
        self.request = request
        self.person = person

class GroupEdited(object):

    def __init__(self, request, person, group, form):
        self.request = request
        self.person = person
        self.group = group
        self.form = form