# -*- coding: utf-8 -*-
#
# Copyright © 2014-2015 Xavier Lamien.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
__author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'


class NewUserRegistered(object):
    """ Event sent when new user signed up. """
    def __init__(self, request, person):
        self.request = request
        self.person = person


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


class ApiRequest(object):
    """ API requests event."""
    def __init__(self, request, data, perm, is_private=False):
        self.is_private = is_private
        self.request = request
        self.data = data
        self.perm = perm


class TokenUsed(object):
    """ Token API acitvity event. """
    def __init__(self, request, perm, person):
        self.request = request
        self.perm = perm
        self.person = person


class NewClientCertificateCreated(object):
    """ New client certificate creation event. """
    def __init__(self, request, person, group_name):
        self.request = request
        self.person = person
        self.group_name = group_name