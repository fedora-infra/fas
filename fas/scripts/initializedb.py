# -*- coding: utf-8 -*-

import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Base,
    AccountStatus,
    RoleLevel,
    )

from fas.models.people import (
    People
    )

from fas.models.group import (
    Groups,
    GroupMembership
    )

from fas.models.configs import (
    AccountPermissions
    )

from fas.security import generate_token

from fas.models import AccountPermissionType as perm


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def fill_account_status():
    status = AccountStatus(id=1, status='Active')
    DBSession.add(status)
    status = AccountStatus(id=3, status='Inactive')
    DBSession.add(status)
    status = AccountStatus(id=5, status='Blocked')
    DBSession.add(status)
    status = AccountStatus(id=6, status='BlockedByAdmin')
    DBSession.add(status)
    status = AccountStatus(id=8, status='Disabled')
    DBSession.add(status)


def fill_role_levels():
    role = RoleLevel(id=0, role='Unknown')
    DBSession.add(role)
    role = RoleLevel(id=1, role='User')
    DBSession.add(role)
    role = RoleLevel(id=2, role='Editor')
    DBSession.add(role)
    role = RoleLevel(id=3, role='Sponsor')
    DBSession.add(role)
    role = RoleLevel(id=5, role='Admin')
    DBSession.add(role)


def create_fake_user(session, upto=2000, user_index=1000):
    from faker import Factory
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
                    bio=fake.paragraph()
                    )
            perms = AccountPermissions(
                        people=people.id,
                        token=generate_token(),
                        application=u'Fedora Mobile v0.9',
                        permissions=perm.CAN_READ_PUBLIC_INFO
                        )
            session.add(people)
            session.add(perms)
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

        create_fake_user(DBSession, upto=13811)
