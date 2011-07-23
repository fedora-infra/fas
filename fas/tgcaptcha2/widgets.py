import pkg_resources
import turbogears as tg
import controller
from tgcaptcha.validator import CaptchaFieldValidator
import gettext
_ = gettext.gettext

from turbogears.widgets import CSSLink, JSLink, Widget, WidgetDescription, \
    register_static_directory, CompoundFormField, FormField, HiddenField
from turbogears import widgets

js_dir = pkg_resources.resource_filename("tgcaptcha",
                                         "static/javascript")
register_static_directory("tgcaptcha", js_dir)

captcha_controller = controller.CaptchaController()

class CaptchaInputField(FormField):
    """Basic captcha widget.
    
    This widget doesn't do any validation, and should only be used if you 
    want to do your own validation.
    """
    template = """
    <span xmlns:py="http://purl.org/kid/ns#">
        <img id="${field_id}_img" 
            src="${controller}/image/${payload}" 
            alt="${alt}"/>
        <input 
            type="text"
            name="${name}"
            class="${field_class}"
            id="${field_id}"
            py:attrs="attrs"/> 
    </span>
    """    
    params = ['controller', 'payload', 'alt', "attrs"] 
    controller = tg.url(tg.config.get("tgcaptcha.controller", "/captcha"))
    alt = _('obfuscated letters')
    attrs = {}
        
class CaptchaField(CompoundFormField):
    "Basic validating captcha widget."
    
    name = 'Captcha'
    fields = [ CaptchaInputField(name='captchainput'),
                HiddenField(name='captchahidden')]
    validator = CaptchaFieldValidator()
            
    def update_params(self, d):
        mwp = d['member_widgets_params']
        payload = captcha_controller.create_payload()
        mwp['payload'] = {'captchainput':payload}
        if not d['value']:
            d['value'] = {'captchahidden':payload}
        else:
            d['value']['captchahidden'] = payload
        super(CaptchaField, self).update_params(d)
        
    template="""
    <span xmlns:py="http://purl.org/kid/ns#">
        <div py:for="field in hidden_fields"
            py:replace="field.display(value_for(field), **params_for(field))" />
        <div py:for="field in fields" py:strip="True">
            <span py:replace="field.display(value_for(field), 
                **params_for(field))"/>
        </div>
    </span>
    """
    
class CaptchaFieldDesc(widgets.WidgetDescription):
    
    name = "CaptchaField"
    for_widget = CaptchaField()
    
__all__ = [ 'CaptchaField', 
            'CaptchaInputField']
    
