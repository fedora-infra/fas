# -*- coding: utf-8 -*-

import os
import sys
import random
import transaction

from sqlalchemy import engine_from_config
from pyramid.i18n import TranslationStringFactory

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from fas.models import (
    DBSession,
    Base,
    AccountStatus,
    RoleLevel,
    )

from fas.models.people import People

from fas.models.group import (
    Groups,
    GroupMembership
    )

from fas.models.configs import AccountPermissions
from fas.models import AccountPermissionType as perm

from fas.security import generate_token

_ = TranslationStringFactory('fas')

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def fill_account_status():
    status = AccountStatus(id=1, status=_(u'Active'))
    DBSession.add(status)
    status = AccountStatus(id=3, status=_(u'Inactive'))
    DBSession.add(status)
    status = AccountStatus(id=5, status=_(u'Blocked'))
    DBSession.add(status)
    status = AccountStatus(id=6, status=_(u'BlockedByAdmin'))
    DBSession.add(status)
    status = AccountStatus(id=8, status=_(u'Disabled'))
    DBSession.add(status)
    status = AccountStatus(id=10, status=_(u'OnVacation'))
    DBSession.add(status)


def fill_role_levels():
    role = RoleLevel(id=0, name=_(u'Unknown'))
    DBSession.add(role)
    role = RoleLevel(id=1, name=_(u'User'))
    DBSession.add(role)
    role = RoleLevel(id=2, name=_(u'Editor'))
    DBSession.add(role)
    role = RoleLevel(id=3, name=_(u'Sponsor'))
    DBSession.add(role)
    role = RoleLevel(id=5, name=_(u'Administrator'))
    DBSession.add(role)


def add_default_user(id, login, name, email, passwd=None, membership=None):
    """ Add a default user into database. """
    pass


def add_default_group():
    """ ADd default group into system."""
    pass


def create_fake_user(session, upto=2000, user_index=1000, group_list=None):
    from faker import Factory
    from fas.utils.avatar import gen_libravatar
    fake = Factory.create()

    users = []
    email = []
    for i in range(0, upto):
        user = fake.profile()
        username = user['username']
        mail = user['mail']
        if (username not in users) and (mail not in email):
            users.append(username)
            email.append(mail)
            people = People(
                    id=user_index,
                    username=username,
                    password=username,
                    fullname=user['name'],
                    email=mail,
                    bio=fake.paragraph(),
                    avatar=gen_libravatar(mail),
                    avatar_id=mail
                    )
            perms = AccountPermissions(
                        people=people.id,
                        token=generate_token(),
                        application=u'Fedora Mobile v0.9',
                        permissions=perm.CAN_READ_PUBLIC_INFO
                        )
            membership = GroupMembership(
                            group_id=random.choice(group_list),
                            people_id=people.id,
                            sponsor=007,
                            role=random.choice([1, 2, 3, 5])
                            )
            session.add(people)
            session.add(perms)
            session.add(membership)
            user_index += 1


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        fill_account_status()
        fill_role_levels()

        # Default values for Dev (could be used for a quick test case as well)
        admin = People(
                    id=007,
                    username=u'admin',
                    password=u'admin',
                    fullname=u'FAS Administrator',
                    email=u'admin@fedoraproject.org'
        )
        user = People(
                    id=999,
                    username=u'foobar',
                    password=u'foobar',
                    fullname=u'FAS User',
                    email=u'user@fedoraproject.org'
        )
        group_admin = Groups(
                        id=2000,
                        name=u'fas-admin',
                        owner_id=admin.id
        )
        group_user = Groups(
                        id=3000,
                        name=u'fas-user',
                        owner_id=user.id
        )
        admin_membership = GroupMembership(
                            group_id=2000,
                            role=5,
                            people_id=admin.id,
                            sponsor=admin.id
        )
        user_membership = GroupMembership(
                            group_id=2000,
                            people_id=user.id,
                            sponsor=admin.id
        )
        admin_token = AccountPermissions(
                        people=admin.id,
                        token=u'498327sdfdj982374239874j34j',
                        application=u'GNOME',
                        permissions=1
        )
        user_token = AccountPermissions(
                        people=user.id,
                        token=u'2342309w8esad09803983i2039e',
                        application=u'IRC Bot - zodbot',
                        permissions=2
        )

        DBSession.add(admin)
        DBSession.add(user)
        DBSession.add(group_admin)
        DBSession.add(group_user)
        DBSession.add(admin_membership)
        DBSession.add(user_membership)
        DBSession.add(user_token)
        DBSession.add(admin_token)

        DBSession.add(Groups(id=300, name=u'avengers', owner_id=admin.id))
        DBSession.add(Groups(id=301, name=u'justice_league', owner_id=user.id))
        DBSession.add(Groups(id=302, name=u'fantastic_four', owner_id=admin.id))
        DBSession.add(Groups(id=303, name=u'all-star', owner_id=user.id))
        DBSession.add(Groups(id=304, name=u'x-men', owner_id=admin.id))

        groups = [3000, 300, 301, 302, 303, 304]
        create_fake_user(DBSession, upto=13811, group_list=groups)
