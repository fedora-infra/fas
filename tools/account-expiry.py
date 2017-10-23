#!/usr/bin/python
__requires__ = 'TurboGears'
import pkg_resources
pkg_resources.require('CherryPy >= 2.0, < 3.0alpha')

import pytz
from datetime import timedelta

import turbogears
from turbogears import config
turbogears.update_config(configfile="/etc/account-expiry.cfg")
import turbomail
from turbogears.database import session
from fas.model import *
from email.Message import Message
import smtplib

# TODO: GPG sign these emails.  
# Maybe we can do it one-time and just include the signature in the message.

WARN_AGE = timedelta(config.get('warn_age'))
MAX_AGE = timedelta(config.get('max_age'))
EXPIRY_TIME = config.get('max_age') - config.get('warn_age')
SMTP_SERVER = config.get('smtp_server')

# Taken (and slightly modified) from Toshio's pkgdb-sync-bugzilla.in in pkgdb
def send_email(fromAddress, toAddress, subject, message, smtp_server=SMTP_SERVER):
    '''Send an email if there's an error.
    
    This will be replaced by sending messages to a log later.
    '''
    msg = Message()
    msg.add_header('To', toAddress)
    msg.add_header('From', fromAddress)
    msg.add_header('Subject', subject)
    msg.set_payload(message)
    smtp = smtplib.SMTP(smtp_server)
    smtp.sendmail(fromAddress, [toAddress], msg.as_string())
    smtp.quit()


if __name__ == '__main__':
    now = datetime.now(pytz.utc)
    
    people = People.query.all()
    whitelist = config.get('whitelist').split(',')
    
    for person in people:
        if person.id < 10000 or person.username in whitelist:
            # Don't disable system accounts or whitelisted accounts
            continue
        if person.status != 'active':
            # They're already deactivated.
            continue
        diff = now - person.last_seen
        if diff > MAX_AGE:
            person.status = 'inactive'
            send_email(config.get('accounts_email'), person.email, 'Fedora Account Expiry', \
            '''Your Fedora Account password has expired, so your account has been
disabled.  To reenable your account, please request a password reset at
https://admin.fedoraproject.org/accounts/user/resetpass.  

If you have any questions, please feel free to contact us at
accounts@fedoraproject.org.

- Fedora Infrastructure Team
''')
        elif diff > WARN_AGE:
            send_email(config.get('accounts_email'), person.email, 'Fedora Account Expiry Warning', \
            '''Your Fedora Account password will expire in %(days)d days.  Please login to
FAS at https://admin.fedoraproject.org/accounts/ as soon as
possible to prevent your account from being disabled.  

- Fedora Infrastructure Team
''')
    
    session.flush()

