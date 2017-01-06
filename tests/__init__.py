import unittest
from datetime import datetime
from decimal import Decimal
import requests
import os
import transaction
from paste.deploy.loadwsgi import appconfig
from pytz import UTC
from sqlalchemy import engine_from_config, create_engine
from fas.lib.avatar import gen_libravatar

here = os.path.dirname(__file__)
settings = appconfig('config:' + os.path.join(here, '../', 'development.ini'))
FAITOUT_URL = 'http://faitout.fedorainfracloud.org'

from fas.scripts.admin import (add_user, add_membership, add_permission,
                               create_default_values)
from fas.models import DBSession, Base
from fas.models.people import People, AccountStatus, AccountPermissionType, \
    PeopleAccountActivitiesLog
from fas.models.configs import AccountPermissions
from fas.models.group import (
    GroupType,
    Groups,
    GroupMembership,
    GroupStatus, MembershipStatus, MembershipRole)
from fas.models.certificates import PeopleCertificates, Certificates
from fas.models.la import LicenseAgreement, LicenseAgreementStatus
from fas.lib.passwordmanager import PasswordManager

pv = PasswordManager()


def empty_db(DBSession):
    DBSession.query(AccountPermissions).delete()

    DBSession.query(GroupMembership).delete()
    DBSession.query(Groups).delete()
    DBSession.query(GroupType).delete()

    DBSession.query(PeopleAccountActivitiesLog).delete()
    DBSession.query(People).delete()
    DBSession.query(PeopleCertificates).delete()

    DBSession.query(Certificates).delete()
    DBSession.query(LicenseAgreement).delete()


def create_groups(DBSession):
    group_type = DBSession.query(GroupType).filter(
        GroupType.name == u'shell').first()

    DBSession.add(
        Groups(
            id=300,
            name=u'avengers',
            status=GroupStatus.ACTIVE.value,
            group_type_id=group_type.id,
            owner_id=007)
    )
    DBSession.add(
        Groups(
            id=301,
            name=u'justice_league',
            status=GroupStatus.ACTIVE.value,
            group_type_id=group_type.id,
            owner_id=007)
    )
    DBSession.add(
        Groups(
            id=302,
            name=u'fantastic_four',
            status=GroupStatus.ACTIVE.value,
            group_type_id=group_type.id,
            owner_id=007)
    )
    DBSession.add(
        Groups(
            id=303,
            name=u'all-star',
            status=GroupStatus.ACTIVE.value,
            group_type_id=group_type.id,
            owner_id=007)
    )
    DBSession.add(
        Groups(
            id=304,
            name=u'x-men',
            status=GroupStatus.ACTIVE.value,
            group_type_id=group_type.id,
            owner_id=007)
    )
    DBSession.flush()

    groups = [300, 301, 302, 303, 304]


def add_users(DBSession):
    user_index = [0, 1, 2]
    username = [u'bob', u'jerry', u'mike']
    gen_pass = pv.generate_password(u'test12')
    passwd = [gen_pass, gen_pass, gen_pass]
    fullname = username
    email = [u'bob@email.com', u'jerbear@test.com', u'm@ike.com']
    postal_address = [u'783 Wiegand Lights Apt. 566\nNorth Marceloview, '
                      u'ND 52464-4628', None, u'487 Brown Greens Apt. '
                                              u'191\nSmithamton, AL 33044-3467']
    introduction = ['hello', 'intro', None]
    avatar = [gen_libravatar(email[0]), gen_libravatar(email[1]), None]
    bio = [None, 'biography of a simple individual', 'i <3 oss']
    privacy = [True, False, True]
    country_code = [u'US', u'FR', u'CA']
    latitude = [43, None, Decimal('85.5335165')]
    longitude = [27, None, Decimal('74.295654')]

    joined = [datetime(2011, 11, 28, 14, 46, 44, tzinfo=UTC),
              datetime(2013, 8, 28, 14, 46, 44, tzinfo=UTC),
              datetime(2016, 2, 28, 14, 46, 44, tzinfo=UTC)]

    status = [8, 1, 3]  # DISABLED, ACTIVE, PENDING
    tokens = ['abcd', '1234', 'xyz']
    group_list = [300, 302, 304]  # avengers, fantastic_four, x-men
    membership_status = [1, 1, 2]  # Approved, Approved, Pending
    membership_role = [4, 2, 1]  # Admin, Editor, User

    for i in range(3):
        people = add_user(
            id=user_index[i],
            login=username[i],
            passwd=passwd[i],
            fullname=fullname[i],
            email=email[i],
            postal_address=postal_address[i],
            introduction=introduction[i],
            avatar=avatar[i],
            avatar_id=email[i],
            bio=bio[i],
            privacy=privacy[i],
            country_code=country_code[i],
            latitude=latitude[i],
            longitude=longitude[i],
            joined=joined[i],
            status=status[i])

        perm = add_permission(
            person_id=people.id,
            token=tokens[i],
            application=u'Fedora Mobile v0.9',
            perms=AccountPermissionType.CAN_READ_PUBLIC_INFO.value
        )
        ms = add_membership(
            group_id=group_list[i],
            person_id=people.id,
            sponsor=007,
            joined=joined[i],
            status=membership_status[i],
            role=membership_role[i]
        )
        people.account_permissions.append(perm)
        people.group_membership.append(ms)
        DBSession.add(people)


def add_license_agreement(DBSession):
    la = LicenseAgreement(name='Test License',
                          status=LicenseAgreementStatus.ENABLED.value,
                          content='You hear by agree to this license for this test',
                          enabled_at_signup=True)
    DBSession.add(la)


from fas import main
from webtest import TestApp


def getDBPath():
    testurl = settings.get('sqlalchemy.url', None) + 'test'
    return testurl

class BaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = main(None, **settings)
        cls.testapp = TestApp(app)
        cls.DB_PATH = getDBPath()
        cls.engine = create_engine(cls.DB_PATH)
        DBSession.configure(bind=cls.engine)
        Base.metadata.create_all(cls.engine)
        cls.DBSession = DBSession

        # empty database if its
        if 'postgres' in cls.DB_PATH.lower() or 'sqlite' in cls.DB_PATH:
            with transaction.manager:
                empty_db(DBSession=cls.DBSession)

    @classmethod
    def tearDownClass(cls):
        if 'postgres' in cls.DB_PATH.lower() and 'faitout' in cls.DB_PATH.lower():
                db_name = cls.DB_PATH.rsplit('/', 1)[1]
                r = requests.get('%s/drop/%s' % (FAITOUT_URL, db_name))  # close the connection
                expected = 'Database ' + db_name + ' has been dropped'
                cls.assertEqual(str(r.text), expected)

    def setUp(self):
        app = main(None, **settings)
        self.testapp = TestApp(app)
        self.populate(self.DBSession)

    def tearDown(self):
        if 'postgres' in self.DB_PATH.lower() or 'sqlite' in self.DB_PATH.lower():
            with transaction.manager:
                empty_db(DBSession=self.DBSession)
        elif 'faitout' in self.DB_PATH.lower():
            db_name = self.DB_PATH.rsplit('/', 1)[1]
            requests.get('%s/clean/%s' % (FAITOUT_URL, db_name))

    def populate(self, db_session):
        admin_pw = u'admin'
        gen_pass = pv.generate_password(admin_pw)
        with transaction.manager:
            # add_default_group_type()
            create_default_values(passwd=gen_pass)
            create_groups(DBSession=db_session)
            add_users(DBSession=db_session)
