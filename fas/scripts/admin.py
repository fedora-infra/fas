# -*- coding: utf-8 -*-
#
# Copyright © 2014-2016 Xavier Lamien.
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
# __author__ = 'Xavier Lamien <laxathom@fedoraproject.org>'

import argparse
import random
import sys
import transaction
from pyramid.i18n import TranslationStringFactory
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)
from sqlalchemy import engine_from_config
from fas.lib.passwordmanager import PasswordManager
from fas.models import (
    DBSession,
    Base,
)
from fas.models.configs import AccountPermissions
from fas.models.group import (
    GroupType,
    Groups,
    GroupMembership,
    GroupStatus, MembershipStatus, MembershipRole)
from fas.models.people import People, AccountStatus, AccountPermissionType
from fas.security import generate_token
from fas.lib.avatar import gen_libravatar

_ = TranslationStringFactory('fas')
__admin_pw__ = u'admin'
__domain__ = u'fedoraproject.org'


def add_default_group_type():
    """ Add standard group type into system."""
    gtype = GroupType(name=u'tracking', comment=u'Tracking people')
    gtype2 = GroupType(name=u'shell', comment=u'Shell access')

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
    user.introduction = introduction
    user.avatar = avatar
    user.avatar_id = avatar_id
    user.bio = bio
    user.privacy = privacy
    user.country_code = country_code
    user.latitude = latitude
    user.longitude = longitude
    user.status = status or AccountStatus.ACTIVE.value
    user.creation_timestamp = joined

    return user


def add_group(id, name, display_name=None, owner_id=None, type=None):
    """ Add a new group into system."""
    group = Groups()
    group.id = id
    group.name = name
    group.display_name = display_name
    group.owner_id = owner_id
    group.group_type = type
    group.parent_group_id = None

    return group


def add_membership(
        group_id, person_id, sponsor=None, joined=None,
        role=MembershipRole.USER.value, status=MembershipStatus.UNAPPROVED.value):
    """ Add a registered user into a registered group.
    :param joined:
    :type joined:
    :param status:
    :type status:
    :param group_id:
    :type group_id:
    :param person_id:
    :type person_id:
    :param sponsor:
    :type sponsor:
    :param role:
    :type role:
    """
    ms = GroupMembership()
    ms.group_id = group_id
    ms.person_id = person_id
    if not sponsor:
        sponsor = person_id
    ms.sponsor_id = sponsor
    ms.role = role
    ms.status = status
    ms.update_timestamp = joined

    return ms


def add_permission(person_id, token=None, application=None, perms=None):
    """ Add permissions to a given user. """
    perm = AccountPermissions()
    perm.person_id = person_id
    perm.token = token
    perm.application = application
    perm.permissions = perms

    return perm


def create_default_values(passwd):
    """ Add a default admin into database. """
    pv = PasswordManager()

    tracking_group = GroupType(name=u'tracking', comment=u'Tracking people')
    shell_group = GroupType(name=u'shell', comment=u'Shell access')

    admin = add_user(
        007,
        u'fasadmin',
        passwd,
        u'FAS Administrator',
        status=AccountStatus.ACTIVE.value,
        introduction=u'The super admin'
    )
    fas_user = add_user(
        999,
        u'jbezorg',
        pv.generate_password(u'jbezorg'),
        u'Jean-Baptiste Emanuel Zorg',
        email=u'88c144de@opayq.com',
        status=AccountStatus.ACTIVE.value,
        avatar=gen_libravatar(u'88c144de@opayq.com'),
        introduction=u'Mr. Zorg The "Art Dealer"'
    )

    admin_group = add_group(id=2000, name=u'fas-admin',
                            display_name=u'Fedora Admin')
    admin_group.group_type = tracking_group
    admin_group.owner = admin
    admin_group.members.append(
        add_membership(
            group_id=admin_group.id,
            role=MembershipRole.ADMINISTRATOR.value,
            status=MembershipStatus.APPROVED.value,
            person_id=admin.id,
            sponsor=admin.id
        )
    )

    fas_group = add_group(id=3000, name=u'fas-user', display_name=u'FAS users')
    fas_group.group_type = tracking_group
    fas_group.owner = fas_user
    fas_group.members.append(
        add_membership(
            group_id=3000,
            role=MembershipRole.USER.value,
            status=MembershipStatus.APPROVED.value,
            person_id=fas_user.id,
            sponsor=fas_user.id
        )
    )

    admin.account_permissions.append(
        add_permission(
            person_id=admin.id,
            token=u'498327sdfdj982374239874j34j',
            application=u'GNOME',
            perms=AccountPermissionType.CAN_READ_PUBLIC_INFO.value
        )
    )

    fas_user.account_permissions.append(
        add_permission(
            person_id=fas_user.id,
            token=u'2342309w8esad09803983i2039e',
            application=u'IRC Bot - zodbot',
            perms=AccountPermissionType.CAN_READ_PEOPLE_PUBLIC_INFO.value
        )
    )

    DBSession.add(shell_group)
    DBSession.add(admin_group)
    DBSession.add(fas_group)


def create_fake_user(session, upto=2000, user_index=1000, group_list=None):
    """ Create a fake user into fas DB. """
    from faker import Factory

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

            people.account_permissions.append(perm)
            people.group_membership.append(ms)
            DBSession.add(people)

            user_index += 1

            if (i % (5 * point) == 0):
                sys.stdout.write(
                    "\r"
                    "Generating fake people: [" + "=" * (i / increment) + " "
                    * ((total - i) / increment) + "]" + str(i / point) + "%")
                sys.stdout.flush()


def authenticate_user(username):
    user = DBSession.query(
        People
    ).filter(
        People.username == username
    ).first()
    user.status = 1


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        description=u'FAS administrative command-line')

    parser.add_argument('-c', '--config',
                        dest='config_file',
                        default='/etc/fas/production.ini',
                        metavar='CONFIG_FILE',
                        help=_(
                            'Specify config file (default '
                            '"/etc/fas/production.ini")'))
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
                        help=_(
                            u'Generate fake data (people & groups) into '
                            u'database.'))
    parser.add_argument('-n', '--people-nb',
                        dest='people_nb',
                        type=int,
                        default=[13811],
                        nargs=1,
                        help=_(u'Define numbers of fake people to generate '
                               'and inject into database.'))
    parser.add_argument('--authenticate-user',
                        dest='authenticate_user',
                        type=str,
                        default='admin',
                        help=_(u'Enter username to manually authenticate'))

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
        if opts.authenticate_user:
            authenticate_user(opts.authenticate_user)
        # fill_account_status()
        # fill_role_levels()

        # Default values for Dev (could be used for a quick test case as well)
        if opts.add_default_value:
            DBSession.query(
                People
            ).filter(People.username == u'fasadmin').delete()

            create_default_values(pv.generate_password(__admin_pw__))

        if opts.gen_fake_data:
            people = DBSession.query(People).all()
            if len(people) > 2:
                print 'Cleaning up People data.'
                DBSession.query(People).delete()
                DBSession.query(Groups).delete()

                create_default_values(
                    pv.generate_password(__admin_pw__))
            elif len(people) == 0:
                create_default_values(
                    pv.generate_password(__admin_pw__))
            else:
                admin = DBSession.query(
                    People
                ).filter(
                    People.username == u'fasadmin'
                ).first()

            group_type = DBSession.query(GroupType).filter(
                GroupType.name == 'shell').first()

            DBSession.add(
                Groups(
                    id=300,
                    name=u'avengers',
                    status=GroupStatus.ACTIVE.value,
                    group_type_id=group_type.id,
                    parent_group_id=None,
                    owner_id=007)
            )
            DBSession.add(
                Groups(
                    id=301,
                    name=u'justice_league',
                    status=GroupStatus.ACTIVE.value,
                    group_type_id=group_type.id,
                    parent_group_id=None,
                    owner_id=007)
            )
            DBSession.add(
                Groups(
                    id=302,
                    name=u'fantastic_four',
                    status=GroupStatus.ACTIVE.value,
                    group_type_id=group_type.id,
                    parent_group_id=None,
                    owner_id=007)
            )
            DBSession.add(
                Groups(
                    id=303,
                    name=u'all-star',
                    status=GroupStatus.ACTIVE.value,
                    group_type_id=group_type.id,
                    parent_group_id=None,
                    owner_id=007)
            )
            DBSession.add(
                Groups(
                    id=304,
                    name=u'x-men',
                    status=GroupStatus.ACTIVE.value,
                    group_type_id=group_type.id,
                    parent_group_id=None,
                    owner_id=007)
            )
            DBSession.flush()

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
            "login: fasadmin\tpassword: %s\n"
            "login: jbezorg\tpassword: jbezorg\n" % __admin_pw__
        )
        sys.stdout.flush()


if __name__ == '__main__':
    main()
