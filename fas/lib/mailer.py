# -*- coding: utf-8 -*-
#
# Copyright © 2014 Pierre-Yves Chibon.
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
__author__ = ['Pierre-Yves Chibon <pingou@fedoraproject.org',
              'Xavier Lamien <laxathom@fedoraproject.org>']

import smtplib
import logging

from email.mime.text import MIMEText

from fas.util import Config


def send_email(message, subject, mail_to, bcc=None, logger=None):  # pragma: no cover
    """
    Sends out email.

    :param message: Email message to send
    :type message: basestring
    :param subject: Email's subject
    :type subject: str
    :param mail_to: email's recipient
    :type mail_to: str or list
    :param bcc: email(s) to add as bcc
    :type bcc: str or list
    :param logger: logging object instance
    :type logger: logging
    """
    msg = MIMEText(message)

    if subject:
        msg['Subject'] = '%s %s' % (Config.get('email.subject_prefix'), subject)
        msg['Subject'].strip()

    from_email = Config.get('email.from')

    if isinstance(mail_to, basestring):
        mail_to = [mail_to]

    msg['From'] = from_email

    if bcc is not None:
        mail_to += bcc
    else:
        msg['To'] = ','.join(mail_to)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(Config.get('email.smtp.server'))

    if logger and logger.isEnabledFor(logging.DEBUG):
        smtp.set_debuglevel(1)

    smtp.sendmail(from_email, mail_to, msg.as_string())
    smtp.quit()

