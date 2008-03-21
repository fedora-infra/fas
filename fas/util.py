import os
import codecs
from turbogears import config
from turbogears.i18n.tg_gettext import get_locale_dir

import logging
# TODO: Is this right?  
log = logging.getLogger('fas.util')

def available_languages():
    """Return available languages for a given domain."""
    available_languages = []
    localedir = get_locale_dir()
    try:
        linguas = codecs.open(os.path.join(localedir, 'LINGUAS'), 'r')
        for lang in linguas.readlines():
            lang = lang.strip()
            if lang and not lang.startswith('#'):
                available_languages.append(lang)
    except IOError, e:
        log.warning('The LINGUAS file could not be opened: %s' % e)
    return available_languages

