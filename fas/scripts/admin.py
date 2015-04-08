# -*- coding: utf-8 -*-
#
# Copyright © 2014 Xavier Lamien.
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
    GroupStatus,
    MembershipRole,
    MembershipStatus,
    AccountPermissionType as PermissionType
)

from fas.models.people import People

from fas.models.group import (
    GroupType,
    Groups,
    GroupMembership
)

from fas.models.configs import AccountPermissions

from fas.lib.passwordmanager import PasswordManager
from fas.security import generate_token

import argparse

_ = TranslationStringFactory('fas')
__admin_pw__ = u'admin'
__domain__ = u'fedoraproject.org'

# def fill_account_status():
# """ Add standard status into system."""
# status = AccountStatus(id=1, status=_(u'Active'))
# DBSession.add(status)
# status = AccountStatus(id=3, status=_(u'Inactive'))
# DBSession.add(status)
# status = AccountStatus(id=5, status=_(u'Blocked'))
#     DBSession.add(status)
#     status = AccountStatus(id=6, status=_(u'BlockedByAdmin'))
#     DBSession.add(status)
#     status = AccountStatus(id=8, status=_(u'Disabled'))
#     DBSession.add(status)
#     status = AccountStatus(id=10, status=_(u'OnVacation'))
#     DBSession.add(status)


# def fill_role_levels():
#     """ Add standard role level into system."""
#     role = RoleLevel(id=0, name=_(u'Unknown'))
#     DBSession.add(role)
#     role = RoleLevel(id=1, name=_(u'User'))
#     DBSession.add(role)
#     role = RoleLevel(id=2, name=_(u'Editor'))
#     DBSession.add(role)
#     role = RoleLevel(id=3, name=_(u'Sponsor'))
#     DBSession.add(role)
#     role = RoleLevel(id=5, name=_(u'Administrator'))
#     DBSession.add(role)


def add_default_group_type():
    """ Add standard group type into system."""
    gtype = GroupType(name=u'tracking', comment='Tracking people')
    gtype2 = GroupType(name=u'shell', comment='Shell access')

    DBSession.add(gtype)
    DBSession.add(gtype2)


def add_user(id, login, passwd, fullname,
             email=None, postal_address=None, joined=None,
             introduction=None, avatar=None, avatar_id=None,
             bio=None, privacy=False, country_code=None,
             latitude=0.0, longitude=0.0, status=None):
    """ Add a user into system. """
    user = People()
    user.id = id
    user.username = login
    user.fullname = fullname
    user.password = passwd
    if email is None:
        email = '%s@%s' % (login, __domain__)
    user.email = email
    user.postal_address = postal_address
    introduction = introduction
    user.avatar = avatar
    user.avatar_id = avatar_id
    user.bio = bio
    user.privacy = privacy
    user.country_code = country_code
    user.latitude = latitude
    user.longitude = longitude
    user.status = status or AccountStatus.ACTIVE
    user.date_created = joined

    DBSession.add(user)

    return user


def add_group(id, name, owner_id, type):
    """ Add a new group into system."""
    group = Groups()
    group.id = id
    group.name = name
    group.owner_id = owner_id
    group.group_type = type

    DBSession.add(group)


def add_membership(
        group_id, people_id, sponsor=None, joined=None,
        role=MembershipRole.USER, status=MembershipStatus.UNAPPROVED):
    """ Add a registered user into a registered group. """
    ms = GroupMembership()
    ms.group_id = group_id
    ms.people_id = people_id
    if not sponsor:
        sponsor = people_id
    ms.sponsor = sponsor
    ms.role = role
    ms.status = status
    ms.approval_timestamp = joined

    DBSession.add(ms)


def add_permission(people_id, token=None, application=None, perms=None):
    """ Add permissions to a given user. """
    perm = AccountPermissions()
    perm.people = people_id
    perm.token = token
    perm.application = application
    perm.permissions = perms

    DBSession.add(perm)


def create_default_admin(passwd):
    """ Add a default admin into database. """
    admin = add_user(
        007,
        u'admin',
        passwd,
        u'FAS administrator',
        status=AccountStatus.ACTIVE
    )

    return admin


def create_default_group(owner):
    """ Create a default group into database. """
    add_default_group_type()

    add_group(
        id=2000,
        name=u'fas-admin',
        owner_id=owner.id,
        type=1
    )

    add_membership(
        group_id=2000,
        role=MembershipRole.ADMINISTRATOR,
        status=MembershipStatus.APPROVED,
        people_id=owner.id,
        sponsor=owner.id
    )


def create_fake_user(session, upto=2000, user_index=1000, group_list=None):
    """ Create a fake user into fas DB. """
    from faker import Factory
    from fas.lib.avatar import gen_libravatar

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
            people = add_user(
                id=user_index,
                login=username,
                passwd=pv.generate_password(username),
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
                longitude=user['current_location'][1],
                joined=fake.date_time_between(start_date='-7y', end_date='-1'),
                status=random.choice([r.value for r in AccountStatus])
            )
            add_permission(
                people_id=people.id,
                token=generate_token(),
                application=u'Fedora Mobile v0.9',
                perms=PermissionType.CAN_READ_PUBLIC_INFO
            )
            add_membership(
                group_id=random.choice(group_list),
                people_id=people.id,
                sponsor=007,
                joined=fake.date_time_between(start_date='-6y', end_date='now'),
                status=random.choice(
                    [s.value for s in MembershipStatus]
                    ),
                role=random.choice(
                    [r.value for r in MembershipRole]
                    )
            )

            user_index += 1

            if(i % (5 * point) == 0):
                sys.stdout.write(
                    "\r"
                    "Generating fake people: [" + "=" * (i / increment) + " "
                    * ((total - i) / increment) + "]" + str(i / point) + "%")
                sys.stdout.flush()


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        description=u'FAS administrative command-line')

    parser.add_argument('-c', '--config',
                        dest='config_file',
                        default='/etc/fas/production.ini',
                        metavar='CONFIG_FILE',
                        help=_(
                            'Specify config file (default "/etc/fas/production.ini")'))
    parser.add_argument('--initdb',
                        dest='initdb',
                        action='store_true',
                        default=False,
                        help=_(u'Initialize fas database'))
    parser.add_argument('--rebuilddb',
                        dest='rebuilddb',
                        action='store_true',
                        default=False,
                        help=_(u'Rebuild fas database from scratch.'))
    parser.add_argument('--default-value',
                        dest='add_default_value',
                        default=False,
                        action='store_true',
                        help=_(u'Inject default value into database.'))

    parser.add_argument('--generate-fake-data',
                        dest='gen_fake_data',
                        action='store_true',
                        default=False,
                        help=_(u'Generate fake data (people & groups) into database.'))
    parser.add_argument('-n', '--people-nb',
                        dest='people_nb',
                        type=int,
                        default=[13811],
                        nargs=1,
                        help=_(u'Define numbers of fake people to generate '
                               'and inject into database.'))

    opts = parser.parse_args()
    config_uri = opts.config_file
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    __domain__ = settings['project.domain.name']

    if opts.rebuilddb:
        Base.metadata.drop_all(engine)
        opts.initdb = True

    if opts.initdb:
        Base.metadata.create_all(engine)

    admin = None
    pv = PasswordManager()

    with transaction.manager:
        #fill_account_status()
        #fill_role_levels()

        # Default values for Dev (could be used for a quick test case as well)
        if opts.add_default_value:
            DBSession.query(
                People
            ).filter(People.username == 'admin').delete()

            admin = create_default_admin(pv.generate_password(__admin_pw__))

            user = add_user(
                999,
                u'jbezorg',
                pv.generate_password(u'jbezorg'),
                u'Jean-Baptiste Emanuel Zorg',
                status=AccountStatus.ACTIVE
            )

            create_default_group(owner=admin)

            add_group(
                id=3000,
                name=u'fas-user',
                owner_id=user.id,
                type=1
            )
            add_membership(
                group_id=3000,
                role=MembershipRole.USER,
                status=MembershipStatus.APPROVED,
                people_id=user.id,
                sponsor=admin.id
            )
            add_permission(
                people_id=admin.id,
                token=u'498327sdfdj982374239874j34j',
                application=u'GNOME',
                perms=PermissionType.CAN_READ_PUBLIC_INFO
            )
            add_permission(
                people_id=user.id,
                token=u'2342309w8esad09803983i2039e',
                application=u'IRC Bot - zodbot',
                perms=PermissionType.CAN_READ_PEOPLE_PUBLIC_INFO
            )

        if opts.gen_fake_data:
            if len(DBSession.query(People).all()) > 2:
                print 'Cleaning up People data.'
                DBSession.query(People).delete()
                DBSession.query(Groups).delete()

                admin = create_default_admin(
                    pv.generate_password(__admin_pw__))
                create_default_group(owner=admin)
            else:
                admin = DBSession.query(
                    People
                ).filter(
                    People.username == 'admin'
                ).first()

            DBSession.add(
                Groups(
                    id=300,
                    name=u'avengers',
                    status=GroupStatus.ACTIVE,
                    group_type=1,
                    owner_id=admin.id)
            )
            DBSession.add(
                Groups(
                    id=301,
                    name=u'justice_league',
                    status=GroupStatus.ACTIVE,
                    group_type=1,
                    owner_id=admin.id)
            )
            DBSession.add(
                Groups(
                    id=302,
                    name=u'fantastic_four',
                    status=GroupStatus.ACTIVE,
                    group_type=2,
                    owner_id=admin.id)
            )
            DBSession.add(
                Groups(
                    id=303,
                    name=u'all-star',
                    status=GroupStatus.ACTIVE,
                    group_type=1,
                    owner_id=admin.id)
            )
            DBSession.add(
                Groups(
                    id=304,
                    name=u'x-men',
                    status=GroupStatus.ACTIVE,
                    group_type=2,
                    owner_id=admin.id)
            )

            groups = [300, 301, 302, 303, 304]

            create_fake_user(
                DBSession,
                upto=int(opts.people_nb[0]),
                group_list=groups
            )

    if opts.add_default_value:
        sys.stdout.write(
            "\nYour database has been created!\n"
            "-------------------------------\n"
            "Default access:\n"
            "login: admin\tpassword: %s\n"
            "login: jbezorg\tpassword: jbezorg\n" % __admin_pw__
        )
        sys.stdout.flush()


if __name__ == '__main__':
    main()
