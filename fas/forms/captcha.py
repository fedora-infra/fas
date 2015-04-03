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

from fas.utils import (
    _,
    Config,
    )
from fas.utils.captcha import Captcha

from wtforms import (
    Form,
    IntegerField,
    HiddenField
    )

from wtforms.validators import (
    Required,
    ValidationError
    )


def check_result(keyname, key=None):

    def __validate__(form, field):
        """ Field validator. """
        captcha = Captcha()
        if Config.get('captcha.secret'):
            keyfield = form[keyname]
            #if not key:
                #raise ValidationError(_(u'You must provide a captcha key.'))
            if not field.data:
                raise ValidationError(_(u'You must provide a captcha value.'))
            if not captcha.validate(keyfield.data, field.data):
                raise ValidationError(_(u'Captcha response is not correct!'))

    return __validate__


class CaptchaForm(Form):
    """ Form to validate captcha. """
    key = HiddenField('key', [Required()])
    captcha = IntegerField(_('Captcha'),
        [Required(), check_result(keyname='key')]
        )