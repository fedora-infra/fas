#-*- coding: utf-8 -*-


from wtforms import Form, HiddenField, StringField, TextAreaField, SelectField, BooleanField, IntegerField, DecimalField, validators


from wtforms import ValidationError

from pytz import common_timezones

from fas.utils import _
from fas.utils import Config

import fas.models.provider as provider
import calendar



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
        raise ValidationError(
            'Field must contain a number')


class EditPeopleForm(Form):
    """ Form to edit user's information. """
    username = StringField(_(u'Username'), [validators.Required()])
    fullname = StringField(_(u'Full name'), [validators.Required()])
    email = StringField(_(u'Email'), [validators.Required(), validators.Email()])
    ircnick = StringField(_(u'IRC nick'))
    avatar = StringField(_(u'Avatar'))
    postal_address = StringField(_(u'Postal address'))
    birthday = IntegerField(_(u'Birthday'))
    birthday_month = SelectField(_(u'Month'),
        choices=[(m, m) for m in calendar.month_name if m is not None])
    bio = TextAreaField(_(u'Introduction'))
    country_code = SelectField(_(u'Country code'),
        [validators.Required()],
        coerce=str,
        choices=[('FR', 'France (FR)'), ('JP', 'Japan (JP)')])
    #FIXME: actually retrieve the list of locales available
    locale = SelectField(_(u'Locale'),
        [validators.Required()],
        choices=[('en', 'en'), ('fr', 'fr')], coerce=str)
    telephone = StringField(_(u'Telephone number'))
    facsimile = StringField(_(u'Facsimile'))
    affiliation = StringField(_(u'Affiliation'))
    timezone = SelectField(_(u'Timezone'),
        [validators.Required()],
        choices=[(tzone, tzone) for tzone in common_timezones])
    gpg_id = StringField(_(u'GPG Key'))
    gpg_fingerprint = StringField(_(u'GPG Fingerprint'))
    ssh_key = StringField(_(u'Public SSH Key'))
    bugzilla_email = StringField(_(u'Bugzilla email'))
    status = SelectField(_(u'Status'),
        [validators.Required()],
        choices=[(stat.account_status.status.capitalize(),
                stat.account_status.status.capitalize())
                 for stat in provider.get_accountstatus()])
    privacy = BooleanField(_(u'Privacy'))
    blog_rss = StringField(_(u'Blog RSS'))
    latitude = DecimalField(_(u'Latitude'))
    longitude = DecimalField(_(u'Longitude'))
