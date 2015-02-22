# -*- coding: utf-8 -*-

import os
import hashlib

from flufl.enum import IntEnum

from pyramid.security import Allow, Everyone

from itsdangerous import JSONWebSignatureSerializer, BadSignature, BadData

from fas import log
from fas.events import LoginSucceeded, LoginFailed, LoginRequested
from fas.models import MembershipStatus, MembershipRole, AccountStatus
from fas.utils import Config
from fas.utils.passwordmanager import PasswordManager

import fas.models.provider as provider
from fas.models import register


def authenticated_is_admin(request):
    """ Validate if authenticated user is an admin.
    :return: True, if admin, false otherwise.
    """
    is_admin = MembershipValidator(
        request.authenticated_userid,
        Config.get_admin_group())

    return is_admin.validate()


def authenticated_is_modo(request):
    """ Validate an authenticated user as a moderator.
    :return: True if modo, false otherwise.
    """
    is_modo = MembershipValidator(
        request.authenticated_userid,
        Config.get_modo_group())

    return is_modo.validate()


def authenticated_is_group_editor(request):
    """ Validate that authenticated user as group editor

    :return: True is user is a group editor, false otherwise.
    """
    is_group_editor = MembershipValidator(
        request.authenticated_userid,
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


def penging_membership_requests(request):
    """ Retrieve membership requests from group where
    authenticated user is at least a sponsor.
    """
    membership = request.get_user.group_membership
    groups = []

    for m in membership:
        if m.role >= MembershipRole.SPONSOR:
            groups.append(m.group_id)

    log.debug(
        'Found %s group where logged user can manage requests membership'
        % len(groups))
    if len(groups) <= 0:
        return groups

    return provider.get_memberships_by_status(MembershipStatus.PENDING, groups)


def join_group(request, group):
    """ Join given group from request object

    :param request: pyramid request object
    :param group: group id
    :type group: integer, `fas.models.group.Group.id`
    """
    register.add_membership(
        group,
        request.get_user.id,
        MembershipStatus.APPROVED
    )


def request_membership(request, group):
    """ Request membership for given group from given person

    :param request: request object
    :param group: id, `fas.models.group.Groups.id`
    :param person: integer, `fas.models.people.People.id`
    """
    register.add_membership(
        group,
        request.get_user.id,
        MembershipStatus.PENDING
        )


def requested_membership(request, group, person):
    """
    Check if authenticated user requested membership already.

    :param request:
    :param group: integer, `fas.models.group.Groups.id`
    :param person: integer, `fas.models.people.People.id`
    :rtype: boolean, true is membership already requested, false otherwise.
    """
    rq = provider.get_memberships_by_status(
        MembershipStatus.PENDING, group, person
    )

    if rq is not None:
        return True

    return False


def remove_membership(request, group):
    """ Remove membership for given group and person

    :param request: pyramid request
    :param group: group id
    :type group: integer, `fas.models.group.Group.id`
    :param person: person id
    :type person: integer, `fas.models.people.People.id`
    """
    register.remove_membership(group, request.get_user.id)


class Root(object):
    def __acl__(self):
        return [
            (Allow, Everyone, 'view'),
            (Allow, self.auth, 'authenticated'),
            (Allow, self.admin, ['admin', 'modo', 'group_edit']),
            (Allow, self.group_editor, 'group_edit'),
            (Allow, self.modo, 'modo')
        ]

    def __init__(self, request):
        """"""
        self.auth = request.authenticated_userid
        self.admin = Config.get_admin_group()
        self.modo = Config.get_modo_group()
        self.group_editor = Config.get_group_editor()


def groupfinder(userid, request):
    """ Retrieve group's membership of authenticated user
    and returns their name.
    """
    user = request.get_user

    if user is not None:
        return [ms.group.name for ms in request.get_user.group_membership]

    return None


class LoginStatus(IntEnum):
    SUCCEED = 0x00
    FAILED = 0x01
    SUCCEED_NEED_APPROVAL = 0x02
    FAILED_INACTIVE_ACCOUNT = 0x03
    FAILED_LOCKED_ACCOUNT = 0x04


def process_login(request, person, password):
    """
    Process login from given login and password

    :param request: pyramid request's object
    :type request: pyramid.request.Request
    :param person: person to process login from
    :type person: fas.models.people.People
    :param password: person password to process login from
    :type password: basestring
    :return: login status
    :rtype: LoginStatus
    """
    notify = request.registry.notify
    blocked = True
    result = LoginStatus.FAILED

    notify(LoginRequested(request, person))

    if person:
        if person.status in [
            AccountStatus.ACTIVE,
            AccountStatus.INACTIVE,
            AccountStatus.ON_VACATION
        ]:
            blocked = False

        pv = PasswordValidator(person, password)

        if pv.is_valid and not blocked:
            # headers = remember(self.request, login)
            request.session.get_csrf_token()

            notify(LoginSucceeded(request, person))

            log.debug('Login succeed for %s' % person.username)
            return LoginStatus.SUCCEED
            # return HTTPFound(location=came_from, headers=headers)

        if person.status == AccountStatus.PENDING:
            result = LoginStatus.PENDING_ACCOUNT
            log.debug('Login failed, account %s has not been validated'
                      % person.username)
        elif person.status in [
            AccountStatus.LOCKED,
            AccountStatus.LOCKED_BY_ADMIN,
            AccountStatus.DISABLED
        ]:
            result = LoginStatus.FAILED_LOCKED_ACCOUNT
            log.debug('Login failed, account %s is blocked' % person.username)
        else:
            notify(LoginFailed(request, person))
            result = LoginStatus.FAILED
            log.debug('Login failed for %s' % person.username)

    return result


def generate_token(length=256):
    """
    Generate token ID.

    :rtype: basestring
    """
    return hashlib.sha1(os.urandom(length)).hexdigest()


class Base(object):
    def __init__(self):
        self.dbsession = None
        self.people = None
        self.token = None
        self.msg = ('Access denied.', 'Unauthorized API key.')

    def set_msg(self, name, text=''):
        """
        Set messages into instantiated object

        :param name: message name
        :param text: message description
        :return: Mone
        """
        self.msg = (name, text)

    def get_msg(self):
        """
        Get message from instantiated object.

        :return: message previously set
        :rtype: (str, str)
        """
        return self.msg


class PasswordValidator(Base):
    def __init__(self, person, password):
        """
        Initialize password validator object.

        :param person: person to check password validation against
        :param password: given password to check validation against
        :return: None
        """
        super(PasswordValidator, self).__init__()
        self.person = person
        self.password = password
        self.pwd_manager = PasswordManager()

    @property
    def is_valid(self):
        """
        Check if password for given login is valid.

        :return:
        true is person and given password at init class match
        with registered one
        :rtype: bool
        """
        if self.person:
            return self.pwd_manager. \
                is_valid_password(self.person.password, self.password)

        return False


class OtpValidator(Base):
    pass


class QAValidator(Base):
    pass


class TokenValidator(Base):
    def __init__(self, request):
        """
        :param request: pyramid request
        :type request: pyramid.Request.request
        :return: None
        """
        super(TokenValidator, self).__init__()
        self.request = request
        self.token = self.request.param_validator.get_apikey()
        self.perm = 0x00
        self.obj = None
        self.msg = ''

    def validate(self):
        """
        Check that api's key is valid.

        :return: true if token is valid, false otherwise
        :rtype: bool
        """
        self.msg = {'', ''}
        log.debug('Looking for valid token: %r' % self.token)
        key = provider.get_account_permissions_by_token(self.token) or \
              provider.get_trusted_perms_by_token(self.token)
        if key:
            self.obj = key
            self.perm = key.permissions
            try:
                self.people = key.account
            except AttributeError:
                log.debug('No people object available for this token')
            return True
        else:
            log.debug('Invalid token, denying access!')
            self.msg = ('Access denied.', 'Unauthorized API key.')

        return False

    def set_token(self, token):
        """
        Set token for validation if not provided
        from class initialization.

        :param token: token to check validation.
        :type token: str
        """
        self.token = token

    def get_obj(self):
        """
        Return token object model.
        :rtype: `fas.models.configs.AccountPermissions`|`fas.models.configs.TrustedPermissions`
        """
        return self.obj

    def get_perm(self):
        """
        Return token related permissions.
        :rtype: `fas.models.AccountPermissionType`
        """
        return self.perm

    def get_owner(self):
        """
        Return validated token's owner.
        :rtype: `fas.models.people.People`
        """
        return self.people


class MembershipValidator(Base):
    """ Validate membership from given group and username"""

    def __init__(self, person_username, group):
        if type(group) is str or unicode:
            self.group = [group]
            # self.group.append(group)
        if type(group) is list:
            self.group = group
        self.username = person_username
        super(MembershipValidator, self).__init__()

    def validate(self):
        """
        Validate membership.

        :return: true if group membership is valid, false otherwise
        """
        groups = provider.get_group_by_people_membership(self.username)

        for group in groups:
            log.debug('checking group membership %s against %s'
                      % (group.name, self.group))
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
            if role:
                if role.role == MembershipRole.ADMINISTRATOR:
                    return True

        return False

    def is_modo(self):
        pass

    def is_sponsor(self):
        """ Check if user is an group sponsor.
        :return: True if user is sponsor, false otherwise.
        """
        if self.validate():
            role = provider.get_membership(self.username, self.group)
            if role:
                if role.role == MembershipRole.SPONSOR:
                    return True

        return False


class ParamsValidator(Base):
    def __init__(self, request, check_apikey=True):
        super(ParamsValidator, self).__init__()
        self.request = request
        self.params = []
        self.apikey = ''
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

    def validate(self):
        """
        Check if request's parameters are valid.

        :returns: True if all given parameters are valid. False otherwise.
        """
        if self.optional_params:
            for p in self.optional_params:
                self.params.append(p)

        if self.request.params:
            for key, value in self.request.params.iteritems():
                log.debug('Validating key %r' % key)
                if key not in self.params:
                    self.set_msg(
                        'Parameter Error.',
                        'Invalid parameter: %r' % str(key)
                    )
                    return False
                else:
                    if not value and (key not in self.optional_params):
                        if key == 'apikey':
                            self.request.response.status = '401 Unauthorized'
                            self.set_msg(
                                'Access denied.',
                                "Required API key is missing.")
                        else:
                            self.set_msg('Invalid parameters', '')
                        log.debug('Missing mandatory key: apikey')
                        return False
                    if key == 'apikey':
                        self.apikey = value
                        log.debug('Found token %r from parameters' % self.apikey)
                    elif key == 'limit':
                        self.limit = value
                    elif key == 'page':
                        self.pagenumber = value
            return True
        else:
            log.debug('Given parameters are invalid')
            self.request.response.status = '400 bad request'
            self.set_msg('Parameter error.', 'No parameter(s) found.')
        return False

    def set_params(self, params):
        self.params.append(params)

    def get_optional(self, optional):
        """ Get optional param's value from request."""
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


class SignedDataValidator(Base):
    def __init__(self, data=None, secret=None):
        """

        :param data: Signed data to validate
        :param secret: The secret used to exchange given data
        :return: None
        """
        super(SignedDataValidator, self).__init__()

        self.data = data
        self.valid_data = None

        if secret is None:
            secret = Config.get('project.api.data.secret')

        self.signer = JSONWebSignatureSerializer(secret)

    def validate(self):
        """
        Validate signed data

        :return: true if data is a valid signed data, false otherwise
        :rtype: bool
        """
        global result

        # self.signer = JSONWebSignatureSerializer(Config.get('project.api.data.secret'))
        try:
            self.valid_data = self.signer.loads(self.data)
            result = True
            log.debug('Get a Valid signed data')
        except BadSignature, e:
            self.set_msg('Access denied', 'Bad signature')
            encoded_payload = e.payload
            result = False

            log.debug('Payload from bad signature: %s' % e.payload)

            if encoded_payload is not None:
                try:
                    self.valid_data = self.signer.load_payload(encoded_payload)
                    result = False
                except BadData:
                    self.set_msg('Invalid request', 'Unexpected signed data')
                    log.debug('Signed data is not valid')
                    result = False

        return result

    def get_data(self):
        """
        Get validated data after being un-serialized

        :return: valid signed data
        :rtype: dict
        """
        return self.valid_data

    @classmethod
    def sign_data(cls, data):
        """
        Sign given data for delivery

        :param data: given data to sign
        :type data: str
        :return: A signed serialized data
        :rtype
        """
        return cls().signer.dumps(data)
