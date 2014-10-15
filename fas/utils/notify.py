# -*- coding: utf-8 -*-


import smtplib
import urlparse

from email.mime.text import MIMEText

from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory('fas')

from fas.utils import Config


def send_email(message, subject, mail_to):  # pragma: no cover
    ''' Send notification by email. '''


    msg = MIMEText(message)

    if subject:
        msg['Subject'] = '[FAS] %s' % subject

    from_email = Config.get('email.from')

    msg['From'] = from_email
    msg['To'] = mail_to

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(Config.get('email.smtp.server'))
    smtp.sendmail(from_email, [mail_to], msg.as_string())
    smtp.quit()


def notify_account_creation(people):
    """ Send an upon notifying the user about his/her account creation.
    """

    base_url = Config.get('project.url')
    validation_url = urlparse.urljoin(
        base_url, '/people/confirm/%s' % people.password_token)

    text = _("""
Welcome!

You have just created an account on the Fedora project Account System (FAS)
at %(url)s.

To complete the account creation, please visit this link:
%(validation_url)s

Sincerely yours,

The Fedora Project
""" % ({
        'url': base_url,
        'validation_url': validation_url,
    }))

    send_email(
        message=text,
        subject=_(
            '[FAS] Confirm account creation for : %(username)s'
            % {'username': people.username}),
        mail_to=people.email,
    )
