# -*- coding: utf-8 -*-
#
# Copyright © 2008  Ricky Zhou
# Copyright © 2011 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Ricky Zhou <ricky@fedoraproject.org>
#            Mike McGrath <mmcgrath@redhat.com>
import os
import codecs

from kitchen.text.converters import to_bytes
import turbomail
from turbogears import config
from turbogears.i18n.tg_gettext import get_locale_dir

import logging
# TODO: Is this right?  
log = logging.getLogger('fas.util')

def available_languages():
    """Return available languages for a given domain."""
    try:
        our_languages = config.get('available_languages')
    except AtributeError:
        our_languages = [
            'en', 'bs', 'cs', 'de', 'el', 'es',
            'fa', 'fr', 'hu', 'id', 'it', 'ja',
            'pl', 'pt_BR', 'ru', 'zh_CN'
        ]

    return our_languages
    # *sigh* Hardcoding is less pain.
    our_languages = []
    localedir = get_locale_dir()
    try:
        linguas = codecs.open(os.path.join(localedir, 'LINGUAS'), 'r')
        for lang in linguas.readlines():
            lang = lang.strip()
            if lang and not lang.startswith('#'):
                our_languages.append(lang)
    except IOError, e:
        log.warning('The LINGUAS file could not be opened: %s' % e)
        our_languages = ['en']
    return our_languages

def send_mail(to_addr, subject, text, from_addr=None):
    if from_addr is None:
        from_addr = config.get('accounts_email')
    message = turbomail.Message(from_addr, to_addr, subject)
    message.plain = text
    if config.get('mail.on', False):
        turbomail.enqueue(message)
    else:
        log.debug('Would have sent: %(subject)s' % {
            'subject': to_bytes(subject)})
        log.debug('To: %(recipients)s' % {
            'recipients': to_bytes(to_addr)})
        log.debug('From: %(sender)s' % {
            'sender': to_bytes(from_addr)})
        log.debug('%s' % to_bytes(text))
