import unittest
import os
from paste.deploy.loadwsgi import appconfig
here = os.path.dirname(__file__)
settings = appconfig('config:' + os.path.join(here, '../', 'test.ini'))
from fas.scripts.admin import add_user
from fas.models import DBSession
from fas.models.people import People, AccountStatus, AccountPermissionType
from fas.models.group import (
    GroupType,
    Groups,
    GroupMembership,
    GroupStatus, MembershipStatus, MembershipRole)

def empty_db():
    DBSession.query(People).delete()
    DBSession.query(Groups).delete()

class BaseTest(unittest.TestCase):
    def setUp(self):
        from fas import main
        app = main(None, **settings)
        from webtest import TestApp
        self.testapp = TestApp(app)

    def populate(self):
        pass

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertTrue(b'Pyramid' in res.body)