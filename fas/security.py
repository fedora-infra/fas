# -*- coding: utf-8 -*-

import os
import hashlib

from pyramid.security import Allow, Everyone

from fas.utils import Config
from fas.utils.passwordmanager import PasswordManager

import fas.models.provider as provider


def authenticated_is_admin(request):
    """ Validate if authenticated user is an admin.
    :return: True, if admin, false otherwise.
    """
    is_admin = MembershipValidator(request.authenticated_userid,
        Config.get_admin_group())

    return is_admin.validate()


def authenticated_is_modo(request):
    """ Validate an authenticated user as a moderator.
    :return: True if modo, false otherwise.
    """
    is_modo = MembershipValidator(request.authenticated_userid,
        Config.get_modo_group())

    return is_modo.validate()


def authenticated_is_group_editor(request):
    """ Validate that authenticated user as group editor

    :return: True is user is a group editor, false otherwise.
    """
    is_group_editor = MembershipValidator(request.authenticated_userid,
        Config.get_group_editor())

    return is_group_editor.validate()


def authenticated_is_group_admin(request, group):
    """ Validate that authenticated user is an group's admin.

    :request: request's object
    :group: group name.
    :return: True if group_admin, false otherwise.
    """
    role = RoleValidator(request.authenticated_userid, group)

    return role.is_admin()


def authenticated_is_group_sponsor(request, group):
    """ Validate that authenticated user is an group's sponsor.

    :request: request's object
    :group: group name
    :return: True if group sponsor, false otherwise.
    """
    role = RoleValidator(request.authenticated_userid, group)

    return role.is_sponsor()


class Root(object):
    def __acl__(self):
        return [
            (Allow, Everyone, 'view'),
            (Allow, self.auth, 'authenticated'),
            (Allow, self.admin, ['admin', 'modo', 'group_edit']),
            (Allow, self.group_editor, 'group_edit'),
            (Allow, self.auth, 'group_edit'),
            (Allow, self.modo, 'modo')
        ]

    def __init__(self, request):
        """"""
        self.auth = request.authenticated_userid
        self.admin = Config.get_admin_group()
        self.modo = Config.get_modo_group()
        self.group_editor = Config.get_group_editor()


def groupfinder(userid, request):
    """ Retrieve group from authenticated user's membership."""
    membership = provider.get_group_by_people_membership(userid)

    groups = []
    for group in membership:
        groups.append(group.name)

    return groups


def generate_token():
    """ Generate an API token. """
    return hashlib.sha1(os.urandom(256)).hexdigest()


class Base(object):

    def __init__(self):
        self.dbsession = None
        self.people = None
        self.token = None
        self.msg = ('Access denied.', 'Unauthorized API key.')

    def set_msg(self, name, text=''):
        self.msg = (name, text)

    def get_msg(self):
        return self.msg


class PasswordValidator(Base):

    def __init__(self, person, password):
        self.person = person
        self.password = password
        self.passwdmanager = PasswordManager()

    def is_valid(self):
        """ Check if password for given login is valid. """
        if self.person:
            return self.passwdmanager.is_valid_password(
                 self.person.password, self.password)
        return False


class OtpValidator(Base):
    pass


class QAValidator(Base):
    pass


class TokenValidator(Base):

    def __init__(self, apikey):
        self.token = apikey
        self.perms = 0
        self.msg = ''

    def is_valid(self):
        """ Check that api's key is valid. """
        self.msg = {'', ''}
        key = provider.get_account_permissions_by_token(self.token)
        if key:
            self.perms = key.permissions
            self.people = key.people
            return True
        else:
            self.msg = ('Access denied.', 'Unauthorized API key.')
        return False

    def set_token(self, token):
        """ Set token for validation. """
        self.token = token

    def get_perms(self):
        """ Get token related permissions. """
        return int(self.perms)

    def get_people_id(self):
        """ Get People's ID from validated token. """
        return self.people


class MembershipValidator(Base):
    """ Validate membership from given group and username"""

    def __init__(self, person_username, group):
        if type(group) is str or unicode:
            self.group = []
            self.group.append(group)
        if type(group) is list:
            self.group = group
        self.username = person_username
        super(MembershipValidator, self).__init__()

    def validate(self):
        """ Validate membership."""
        membership = provider.get_group_by_people_membership(self.username)

        for group in membership:
            if group.name in self.group:
                return True

        return False


class RoleValidator(MembershipValidator):

    def __init__(self, username, group):
        super(RoleValidator, self).__init__(username, group)
        self.username = username
        self.group = group
        self.group_admin = Config.get_admin_group()
        self.group_modo = Config.get_modo_group()

    def is_admin(self):
        """ Check if user is an admin.
        :return: true if user is admin, false otherwise.
        """
        if self.validate():
            role = provider.get_membership(self.username, self.group)
            if role and role.role == 5:
                return True

        return False

    def is_modo(self):
        pass

    def is_sponsor(self):
        pass


class ParamsValidator(Base):

    def __init__(self, request, check_apikey=False):
        self.request = request
        self.params = []
        self.apikey = ''
        # maybe we should let admin configure this limit?
        self.limit = 200
        self.pagenumber = 1
        self.optional_params = []
        self.msg = ()

        if check_apikey:
            self.params.append(u'apikey')

    def __set_msg__(self, name, text=''):
        self.msg = (name, text)

    def add_optional(self, optional):
        """ Add optional parameter to validate.

        :args optional: string, requested optional parameter.
        """
        self.optional_params.append(unicode(optional))

    def add_param(self, params):
        """ Add mandatory parameter to validate.

        :arg params: string, requested madatory parameter.
        """
        self.params.append(unicode(params))

    def is_valid(self):
        """ Check if request's parameters are valid.

        :returns: True if all given parameters are valid. False otherwise.
        """
        if self.optional_params:
            for p in self.optional_params:
                self.params.append(p)

        if self.request.params:
            for key, value in self.request.params.iteritems():
                if key not in self.params:
                    self.set_msg('Parameter Error.',
                                    'Invalid parameter: %r' % str(key))
                    return False
                else:
                    if not value and (key not in self.optional_params):
                        if key == 'apikey':
                            self.request.response.status = '401 Unauthorized'
                            self.set_msg('Access denied.',
                                            "Required API key is missing.")
                        else:
                            self.set_msg('Invalid parameters', '')
                        return False
                    if key == 'apikey':
                        self.apikey = value
                    elif key == 'limit':
                        self.limit = value
                    elif key == 'page':
                        self.pagenumber = value
            return True
        else:
            self.request.response.status = '400 bad request'
            self.set_msg('Parameter error.', 'No parameter(s) found.')
        return False

    def set_params(self, params):
        self.params.append(params)

    def get_optional(self, optional):
        """ Get request optional param value."""
        try:
            return self.request.params.getone(unicode(optional))
        except KeyError:
            return None

    def get_apikey(self):
        """ Get API key value from request parameter. """
        return str(self.apikey)

    def get_limit(self):
        """ Get items limit per requests. """
        return int(self.limit)

    def get_pagenumber(self):
        """ Get page index for pagination. """
        return int(self.pagenumber)

    def get_msg(self):
        """ Get error messages from a validation check.

        :returns: tuple object of error message if is_valid() is False,
                  None otherwise.
        """
        return self.msg