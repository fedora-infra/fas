# -*- coding: utf-8 -*-
"""
    TODO:
        Move notification messages to `fas.notifications`
        upgrading `fas.utils.notify` as a lib we can re-use as
        3rd-party.
"""

import smtplib
import logging

from email.mime.text import MIMEText

from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('fas')

from fas.utils import Config


def send_email(message, subject, mail_to, logger=None):  # pragma: no cover
    ''' Send notification by email. '''

    msg = MIMEText(message)

    if subject:
        msg['Subject'] = '[FAS] %s' % subject

    from_email = Config.get('email.from')

    if isinstance(mail_to, basestring):
        mail_to = [mail_to]

    msg['From'] = from_email
    msg['To'] = ','.join(mail_to)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(Config.get('email.smtp.server'))

    if logger:
        if logger.isEnabledFor(logging.DEBUG):
            smtp.set_debuglevel(1)

    smtp.sendmail(from_email, mail_to, msg.as_string())
    smtp.quit()

