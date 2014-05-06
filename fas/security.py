
import os
import hashlib
import fas.models.provider as provider

USERS = {'admin':'admin',
          'viewer':'viewer'}
GROUPS = {'admin':['group:admin']}


def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])


def generate_token():
    """ Generate an API token. """
    return hashlib.sha1(os.urandom(256)).hexdigest()


class Base:

    def __init__(self):
        self.dbsession = None
        self.people = None
        self.token = None
        self.msg = ()

    def set_msg(self, name, text=''):
        self.msg = (name, text)

    def get_msg(self):
        return self.msg


class PasswordValidator(Base):
    pass


class OtpValidator(Base):
    pass


class QAValidator(Base):
    pass


class TokenValidator(Base):

    def __init__(self, dbsession, apikey):
        self.dbsession = dbsession
        self.token = apikey
        self.perms = None
        self.msg = ''

    def is_valid(self):
        """ Check that api's key is valid. """
        self.msg = {'', ''}
        key = provider.get_account_permissions_by_token(
            self.dbsession, self.token
            )
        if key:
            print 'Found token in database'
            self.perms = key.permissions
            self.people = key.people
            return True
        else:
            self.msg = ('Access denied.', 'Unauthorized API key.')
        return False

    def set_token(self, token):
        self.token = token

    def get_perms(self):
        """ Get token related permissions. """
        return self.perms

    def get_people_id(self):
        """ Get People's ID from validated token. """
        return self.people
