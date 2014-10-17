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
        base_url, '/register/confirm/%s' % people.password_token)

    text = _("""
Welcome!

You have just created an account on the %(organisation)s Account System (FAS)
at %(url)s.

To complete the account creation, please visit this link:
%(validation_url)s

Sincerely yours,

The %(organisation)s
""" % ({
        'organisation': Config.get('project.organisation'),
        'url': base_url,
        'validation_url': validation_url,
    }))

    send_email(
        message=text,
        subject=_(
            '%(username)s please confirm your %(project_name)s account'
            % {
                'username': people.username,
                'project_name': Config.get('project.name'),
            }),
        mail_to=people.email,
    )
