# -*- coding: utf-8 -*-

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