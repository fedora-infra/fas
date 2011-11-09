from turbogears.validators import Schema, Invalid, FormValidator, \
    String
from fas.tgcaptcha2 import controller
import gettext
from turbogears import config
from datetime import datetime

_ = gettext.gettext

captcha_controller = controller.CaptchaController()


class ValidCaptchaInput(FormValidator):

    messages = {'incorrect': _("Incorrect value."),
                'timeout': _("Too much time elapsed. Please try again.")}

    __unpackargs__ = ('captchahidden', 'captchainput')

    timeout = int(config.get('tgcaptcha.timeout', 5))

    def validate_python(self, field_dict, state):
        hidden = str(field_dict['captchahidden'])
        input_val = str(field_dict['captchainput'])
        try:
            payload = captcha_controller.model_from_payload(hidden)
        except:
            raise Invalid(self.message('incorrect', state), field_dict, state)
        if payload.plaintext != input_val:
            raise Invalid(self.message('incorrect', state), field_dict, state)
        elapsed = datetime.utcnow() - payload.created
        if elapsed.seconds > self.timeout * 60:
            raise Invalid(self.message('timeout', state), field_dict, state)


class CaptchaFieldValidator(Schema):

    captchahidden = String(min=44, max=44)
    captchainput = String(not_empty=True)

    chained_validators = [ValidCaptchaInput('captchahidden', 'captchainput')]
