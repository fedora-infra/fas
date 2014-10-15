# -*- coding: utf-8 -*-

import os
import sys
import random
import transaction

from time import sleep

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
    MembershipRole,
    AccountPermissionType as PermissionType
    )

from fas.models.people import People

from fas.models.group import (
    GroupType,
    Groups,
    GroupMembership
    )

from fas.models.configs import AccountPermissions
from fas.models import AccountPermissionType as perm

from fas.utils.passwordmanager import PasswordManager
from fas.security import generate_token


_ = TranslationStringFactory('fas')


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


#def fill_account_status():
    #""" Add standard status into system."""
    #status = AccountStatus(id=1, status=_(u'Active'))
    #DBSession.add(status)
    #status = AccountStatus(id=3, status=_(u'Inactive'))
    #DBSession.add(status)
    #status = AccountStatus(id=5, status=_(u'Blocked'))
    #DBSession.add(status)
    #status = AccountStatus(id=6, status=_(u'BlockedByAdmin'))
    #DBSession.add(status)
    #status = AccountStatus(id=8, status=_(u'Disabled'))
    #DBSession.add(status)
    #status = AccountStatus(id=10, status=_(u'OnVacation'))
    #DBSession.add(status)


#def fill_role_levels():
    #""" Add standard role level into system."""
    #role = RoleLevel(id=0, name=_(u'Unknown'))
    #DBSession.add(role)
    #role = RoleLevel(id=1, name=_(u'User'))
    #DBSession.add(role)
    #role = RoleLevel(id=2, name=_(u'Editor'))
    #DBSession.add(role)
    #role = RoleLevel(id=3, name=_(u'Sponsor'))
    #DBSession.add(role)
    #role = RoleLevel(id=5, name=_(u'Administrator'))
    #DBSession.add(role)


def add_default_group_type():
    """ Add standard group type into system."""
    gtype = GroupType(name=u'tracking', description='Tracking people')
    gtype = GroupType(name=u'shell', description='Shell access')
    DBSession.add(gtype)


def add_default_user(id, login, name, email, passwd=None, membership=None):
    """ Add a default user into system. """
    pass


def add_default_group():
    """ Add default group into system."""
    pass


def create_fake_user(session, upto=2000, user_index=1000, group_list=None):
    """ Create a fake user into fas DB. """
    from faker import Factory
    from fas.utils.avatar import gen_libravatar
    fake = Factory.create()

    pv = PasswordManager()

    users = []
    email = []
    total = upto
    point = total / 100
    increment = total / 20
    sys.stdout.write('\n')
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
                password=pv.generate_password(username),
                fullname=user['name'],
                email=mail,
                postal_address=user['address'],
                introduction=fake.sentence(),
                avatar=gen_libravatar(mail),
                avatar_id=mail,
                bio=fake.paragraph(variable_nb_sentences=True),
                privacy=fake.boolean(),
                country_code=fake.country_code(),
                latitude=user['current_location'][0],
                longitude=user['current_location'][1]
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
                role=random.choice(
                    [r.value for r in MembershipRole]
                )
            )
            session.add(people)
            session.add(perms)
            session.add(membership)
            user_index += 1

            if(i % (5 * point) == 0):
                sys.stdout.write(
                    "\r"
                    "Generating fake people: [" + "=" * (i / increment) + " "
                    * ((total - i) / increment) + "]" + str(i / point) + "%")
                sys.stdout.flush()


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    pv = PasswordManager()
    with transaction.manager:
        #fill_account_status()
        #fill_role_levels()

        # Default values for Dev (could be used for a quick test case as well)
        admin = People(
            id=007,
            username=u'admin',
            password=pv.generate_password('admin'),
            fullname=u'FAS Administrator',
            email=u'admin@fedoraproject.org'
        )
        user = People(
            id=999,
            username=u'foobar',
            password=pv.generate_password('foobar'),
            fullname=u'FAS User',
            email=u'user@fedoraproject.org'
        )
        group_admin = Groups(
            id=2000,
            name=u'fas-admin',
            owner_id=admin.id,
            group_type=2
        )
        group_user = Groups(
            id=3000,
            name=u'fas-user',
            owner_id=user.id,
            group_type=1
        )
        admin_membership = GroupMembership(
            group_id=2000,
            role=MembershipRole.ADMINISTRATOR,
            people_id=admin.id,
            sponsor=admin.id
        )
        user_membership = GroupMembership(
            group_id=2000,
            role=MembershipRole.USER,
            people_id=user.id,
            sponsor=admin.id
        )
        admin_token = AccountPermissions(
            people=admin.id,
            token=u'498327sdfdj982374239874j34j',
            application=u'GNOME',
            permissions=PermissionType.CAN_READ_PUBLIC_INFO
        )
        user_token = AccountPermissions(
            people=user.id,
            token=u'2342309w8esad09803983i2039e',
            application=u'IRC Bot - zodbot',
            permissions=PermissionType.CAN_READ_PEOPLE_PUBLIC_INFO
        )

        DBSession.add(admin)
        DBSession.add(user)
        DBSession.add(group_admin)
        DBSession.add(group_user)
        DBSession.add(admin_membership)
        DBSession.add(user_membership)
        DBSession.add(user_token)
        DBSession.add(admin_token)


        DBSession.add(Groups(
            id=300, name=u'avengers', group_type=1, owner_id=admin.id))
        DBSession.add(Groups(
            id=301, name=u'justice_league', group_type=1, owner_id=user.id))
        DBSession.add(Groups(
            id=302, name=u'fantastic_four', group_type=2, owner_id=admin.id))
        DBSession.add(
            Groups(id=303, name=u'all-star', group_type=1, owner_id=user.id))
        DBSession.add(
            Groups(id=304, name=u'x-men', group_type=2, owner_id=admin.id))

        groups = [3000, 300, 301, 302, 303, 304]
        create_fake_user(DBSession, upto=13811, group_list=groups)
