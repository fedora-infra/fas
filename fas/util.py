import os
import codecs
from turbogears import config
from turbogears.i18n.tg_gettext import get_locale_dir

def available_languages():
    """Return available languages for a given domain."""
    available_languages = []
    localedir = get_locale_dir()
    linguas = codecs.open(os.path.join(localedir, 'LINGUAS'), 'r')
    for lang in linguas.readlines():
        lang = lang.strip()
        if lang and not lang.startswith('#'):
            available_languages.append(lang)
    return available_languages

