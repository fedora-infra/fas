#-*- coding: utf-8 -*-

import wtforms
from pytz import common_timezones

from fas.models import DBSession
import fas.models.provider as provider


## Yes we do nothing with the form argument but it's required...
# pylint: disable=W0613
def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    if not field.data:
        return
    try:
        float(field.data)
    except ValueError:
        raise wtforms.ValidationError(
            'Field must contain a number')


class EditPeopleForm(wtforms.Form):
    """ Form to edit user's information. """
    username = wtforms.TextField(
        'Username<span class="error">*</span>',
        [wtforms.validators.Required()])
    email = wtforms.TextField(
        'Email<span class="error">*</span>',
        [wtforms.validators.Required()])
    ircnick = wtforms.TextField('IRC nick')
    avatar = wtforms.TextField('Avatar')
    post_address = wtforms.TextField('Postal address')
    #FIXME: actually retrieve a list of Country code
    country_code = wtforms.SelectField(
        'Country code',
        [wtforms.validators.Required()],
        choices=[('en', 'en')])
    #FIXME: actually retrieve the list of locales available
    locale = wtforms.SelectField(
        'Locale',
        [wtforms.validators.Required()],
        choices=[('en', 'en')])
    telephone = wtforms.TextField('Telephone number')
    facsimile = wtforms.TextField('Facsimile')
    affiliation = wtforms.TextField('Affiliation')
    comment = wtforms.TextField('Comments')
    timezone = wtforms.SelectField(
        'Timezone',
        [wtforms.validators.Required()],
        choices=[(tzone, tzone) for tzone in common_timezones])
    gpg_id = wtforms.TextField('GPG Key ID')
    ssh_key = wtforms.TextField('Public RSA SSH Key')
    bugzilla_email = wtforms.TextField('Bugzilla email')
    status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[(stat.account_status.status.capitalize(),
                stat.account_status.status.capitalize())
                 for stat in provider.get_accountstatus(DBSession)])
    privacy = wtforms.BooleanField('Privacy')
    blog_rss = wtforms.TextField('Blog RSS')
    latitude = wtforms.TextField('Latitude', [is_number])
    longitude = wtforms.TextField('Longitude', [is_number])

