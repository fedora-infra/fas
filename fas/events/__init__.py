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


class PasswordChangeRequested(object):
    """ Password change request event. """
    def __init__(self, request, person):
        self.request = request
        self.person = person


class GroupEdited(object):

    def __init__(self, request, person, group, form):
        self.request = request
        self.person = person
        self.group = group
        self.form = form

class GroupRemovalRequested(object):
    """ Group removal event. """
    def __init__(self, request, group_id):
        self.request = request
        self.group = group_id

class GroupTypeRemovalRequested(object):
    """ Group type removal event. """
    def __init__(self, request, grouptype_id):
        self.request = request
        self.grouptype = grouptype_id


class LicenseRemovalRequested(object):
    """ license agreement removal event. """
    def __init__(self, request, license_id):
        self.request = request
        self.license = license_id


class TokenUsed(object):
    """ Token API acitvity event. """
    def __init__(self, request, perm, person):
        self.request = request
        self.perm = perm
        self.person = person