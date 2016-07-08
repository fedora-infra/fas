import unittest
from datetime import datetime
from decimal import Decimal

import os
from paste.deploy.loadwsgi import appconfig

from fas.lib.avatar import gen_libravatar

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

def create_groups():
    group_type = DBSession.query(GroupType).filter(
        GroupType.name == 'shell').first()

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


def add_users(group_id):
    user_index = [0, 1, 2]
    username = ['bob', 'jerry', 'mike']
    passwd = ['test12', 'test12', 'test12']
    fullname = username
    email = ['bob@email.com', 'jerbear@test.com', 'm@ike.com']
    postal_address = [u'783 Wiegand Lights Apt. 566\nNorth Marceloview, '
                      u'ND 52464-4628', None, u'487 Brown Greens Apt. '
                                              u'191\nSmithamton, AL 33044-3467']
    introduction = ['hello', 'intro', None]
    avatar = [gen_libravatar(email[0]), gen_libravatar(email)[1], None]
    bio = [None, 'biography of a simple individual', 'i <3 oss']
    privacy = [1, 0, 1]
    country_code = ['US', 'FR', 'CA']
    latitude = [43, None, Decimal('85.5335165')]
    longitude = [27, None, Decimal('74.295654')]
    joined = [datetime(2011, 11, 28, 14, 46, 44),
              datetime(2013, 8, 28, 14, 46, 44),
              datetime(2016, 2, 28, 14, 46, 44)
              ]
    status = [8, 1, 1]

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
            token=generate_token(),
            application=u'Fedora Mobile v0.9',
            perms=AccountPermissionType.CAN_READ_PUBLIC_INFO.value
        )
        ms = add_membership(
            group_id=random.choice(group_list),
            person_id=people.id,
            sponsor=007,
            joined=fake.date_time_between(start_date='-6y', end_date='now'),
            status=random.choice(
                [s.value for s in MembershipStatus]
            ),
            role=random.choice(
                [r.value for r in MembershipRole]
            )
        )
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