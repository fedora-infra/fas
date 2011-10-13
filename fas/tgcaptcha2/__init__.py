from paste.script import templates
import pkg_resources

from widgets import *

class TGCaptchaConfig(templates.Template):

    egg_plugins = ['TGCaptchaConfig']
    _template_dir = pkg_resources.resource_filename("fas.tgcaptcha2", "template")
    summary = "Provides a configuration file template for TGCaptcha"
    required_templates = ['tgbase']
    use_cheetah = False
