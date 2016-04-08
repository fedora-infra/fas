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

from fas.models import DBSession as session
from fas.models.people import PeopleAccountActivitiesLog
from fas.models.configs import AccountPermissions, TrustedPermissions
from fas.models.group import Groups, GroupType, MembershipStatus, MembershipRole
from fas.models.group import GroupMembership
from fas.models.la import LicenseAgreement, SignedLicenseAgreement
from fas.models.certificates import Certificates, ClientsCertificates

from fas.util import _
from fas.lib.passwordmanager import PasswordManager
from fas.lib.geoip import get_record_from

from ua_parser import user_agent_parser

import logging

log = logging.getLogger(__name__)


def flush():
    """ Flush the database session. """
    session.flush()


def save_account_activity(request, people, event, msg=None):
    """ Register account activity. """
    remote_ip = request.client_addr

    record = get_record_from(remote_ip)
    log.debug('Found record from remote IP(%s): %s' % (remote_ip, record))

    user_agent = user_agent_parser.Parse(request.headers['User-Agent'])
    log.debug('Parsing user_agent: %s' % user_agent)

    client = user_agent['user_agent']['family']
    log.debug('Found clien from user_agent: %s' % client)

    device = user_agent['device']['family']
    log.debug('Found device from user_agent: %s' % device)

    if client != 'Other':
        client = client
        if device != 'Other':
            client = client + ' on %s' % device
    else:
        client = user_agent['string']
        log.debug('Using user_agent as client: %s' % client)

    if record:
        city = record['city']
        log.debug('Found city in IP record: %s' % city)

        country = '%s (%s)' % (record['country_name'], record['country_code3'])
        log.debug('Found country in IP record: %s' % country)

        if city:
            location = '%s, %s' % (city, country)
        else:
            location = country
    else:
        location = _('Unknown')

    log.debug('Set remote location to: %s' % location)

    activity = PeopleAccountActivitiesLog(
        people=people,
        location=location,
        access_from=client,
        remote_ip=remote_ip,
        event=event,
        event_msg=msg
        )

    session.add(activity)


def add_token(
        description,
        token,
        permission,
        people_id=None,
        trusted=False,
        secret=None):
    """
    Add given token to database.

    :param description: A description for the token
    :type description: str
    :param token: The token to store
    :type token: basestring
    :param permission: Level of permission for token
    :type permission: `fas.models.people.AccountPermissionType`
    :param people_id: People id to attach token to
    (required if not trusted token)
    :type people_id: int
    :param trusted: Set given token as trusted
    :type trusted: bool
    :param secret: A secret token to attach to a trusted token
    :type secret: basestring
    """
    if trusted:
        perm = TrustedPermissions()
        perm.secret = secret
    else:
        perm = AccountPermissions()
        perm.people = people_id

    perm.token = token
    perm.application = description
    perm.permissions = permission

    session.add(perm)


def add_people(people):
    """ Add new people obj into databse. """
    session.add(people)


def add_grouptype(form):
    """ Add group type into database."""
    grouptype = GroupType()
    grouptype.name = form.name.data
    grouptype.comment = form.comment.data

    session.add(grouptype)
    session.flush()
    session.refresh(grouptype)

    return grouptype


def add_group(form):
    """ Add group from given form.

    :param form: Populated group edition form.
    :type form: fas.forms.group.EditGroupForm
    :return: Stored Groups object
    :rtype: fas.models.group.Groups
    """
    group = Groups()
    group.name = form.name.data
    group.display_name = form.display_name.data
    group.description = form.description.data
    # Disable now.
    # group.avatar = form.avatar.data
    group.web_link = form.web_link.data
    group.mailing_list = form.mailing_list.data
    group.mailing_list_url = form.mailing_list_url.data
    group.irc_channel = form.irc_channel.data
    group.irc_network = form.irc_network.data
    group.owner_id = form.owner_id.data
    group.group_type = form.group_type.data
    group.parent_group_id = form.parent_group_id.data
    group.private = form.private.data
    group.self_removal = form.self_removal.data
    group.need_approval = form.need_approval.data
    group.invite_only = form.invite_only.data
    group.join_msg = form.join_msg.data
    group.apply_rules = form.apply_rules.data
    group.bound_to_github = form.bound_to_github.data
    group.license_sign_up = form.license_sign_up.data
    group.requires_sponsorship = form.requires_sponsorship.data
    group.requires_ssh = form.requires_ssh.data

    # Add default membership for group's owner
    group.members.append(
        GroupMembership(
            group_id=group.id,
            people_id=group.owner_id,
            status=MembershipStatus.APPROVED.value,
            role=MembershipRole.ADMINISTRATOR.value
        )
    )

    session.add(group)
    session.flush()
    session.refresh(group)

    return group


def add_membership(group_id, people_id, status, role=None, sponsor=None):
    """ Add given people to group"""
    membership = GroupMembership()
    membership.group_id = group_id
    membership.people_id = people_id
    membership.status = status
    membership.sponsor = sponsor or people_id

    if role:
        membership.role = role

    session.add(membership)
    session.flush()


def add_license(form):
    """
    Add new license into database.

    :form: EditLicenseForm which contains license object
    :rtype: :class: `fas.models.la.LicenseAgreement`
    """
    la = LicenseAgreement()
    la.name = form.name.data
    la.content = form.content.data
    la.comment = form.comment.data

    session.add(la)
    session.flush()
    session.refresh(la)

    return la


def remove_license(license_id):
    """ Remove given license from database.

    :id: license id
    """
    session.query(
        LicenseAgreement
    ).filter(
        LicenseAgreement.id == license_id
    ).delete()


def add_signed_license(form):
    """ Add a signed license to database. """
    la = SignedLicenseAgreement()
    la.license = form.license.data
    la.people = form.people.data
    la.signed = form.signed.data

    session.add(la)


def update_password(form, people):
    """ Update password."""
    pm = PasswordManager()
    form.password.data = pm.generate_password(form.password.data)
    form.populate_obj(people)


def remove_grouptype(type_id):
    """ Remove group type from database. """
    session.query(GroupType).filter(GroupType.id == type_id).delete()


def remove_group(group):
    """ Remove group from database."""
    # session.query(Groups).filter(Groups.id == group_id).delete()
    session.delete(group)
    session.flush()


def remove_token(id):
    """ Remove people's token from database. """
    session.query(AccountPermissions).filter_by(id=id).delete()


def remove_membership(group, person):
    """ Remove membership request from pending list

    :param group: group id
    :typpe group: integer, `fas.models.Groups.id`
    :param person: person id
    :type person: integer, `fas.models.People.id`
    """
    session.query(
        GroupMembership
        ).filter(
            GroupMembership.group_id == group,
            GroupMembership.people_id == person
        ).delete()


def add_certificate(form):
    """
    Add new certificate into database.

    :form: `EditCertificateForm` which contains license object
    :rtype: :class: `fas.models.la.LicenseAgreement`
    """
    cert = Certificates()
    cert.name = form.name.data
    cert.description = form.description.data
    cert.cert = form.cert.data
    cert.cert_key = form.cert_key.data
    cert.client_cert_desc = form.client_cert_desc.data
    cert.enabled = form.enabled.data

    session.add(cert)
    session.flush()
    session.refresh(cert)

    return cert


def add_client_certificate(ca, people, cert, serial):
    """
    Add client certificate from given CA and people.

    :ca: `fas.models.certificates.Certificates`
    :people: `fas.models.people.People`
    :cert: client certificate to store.
    :serial: client certificate serial to store.
    """
    ccert = ClientsCertificates()
    ccert.ca = ca.id
    ccert.people = people.id
    ccert.serial = serial
    ccert.certificate = cert

    session.add(ccert)


def add_trusted_token():
    """
    Add trusted token

    :return:
    """
    return None

def remove_trusted_token(id):
    """
    Deletes a trusted token from the system.
    :param id: Token id to look up
    :type id: str
    :return:
    :rtype:
    """
    session.query(TrustedPermissions).filter_by(id=id).delete()
