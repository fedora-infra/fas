# -*- coding: utf-8 -*-

from fas.models import DBSession as session
from fas.models.people import PeopleAccountActivitiesLog

from fas.utils import _
from fas.utils.geoip import get_record_from

from ua_parser import user_agent_parser


def save_account_activity(request, people, event):
    """ Register account activity. """
    remote_ip = request.client_addr
    record = get_record_from(remote_ip)
    #record = get_record_from('86.70.6.26') # test IP

    user_agent = user_agent_parser.Parse(request.headers['User-Agent'])
    client = user_agent['user_agent']['family']
    device = user_agent['device']['family']

    if client != 'Other':
        client = client
        if device != 'Other':
            client = client + ' on %s' % device
    else:
        client = user_agent['string']

    if record:
        city = record['city']
        country = '%s (%s)' % (record['country_name'], record['country_code3'])

        if city:
            location = '%s, %s' % (city, country)
        else:
            location = country
    else:
        location = _('Unknown')

    activity = PeopleAccountActivitiesLog(
        people=people,
        location=location,
        access_from=client,
        remote_ip=remote_ip,
        event=event
        )

    session.add(activity)