import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Base,
    AccountStatus,
    RoleLevel,
    )

from ..models.people import (
    People
)

from ..models.group import (
    GroupType,
    Groups
)

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def fill_account_status():
    status = AccountStatus(id=1, status='Active')
    DBSession.add(status)
    status = AccountStatus(id=3, status='Inactive')
    DBSession.add(status)
    status = AccountStatus(id=5, status='Blocked')
    DBSession.add(status)
    status = AccountStatus(id=8, status='Disabled')
    DBSession.add(status)


def fill_role_levels():
    role = RoleLevel(id=0, role='Unknown')
    DBSession.add(role)
    role = RoleLevel(id=1, role='User')
    DBSession.add(role)
    role = RoleLevel(id=2, role='Editor')
    DBSession.add(role)
    role = RoleLevel(id=3, role='Sponsor')
    DBSession.add(role)
    role = RoleLevel(id=5, role='Admin')
    DBSession.add(role)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        fill_account_status()
        fill_role_levels()
#        admin = User(name=u'admin', password=u'admin')
#        DBSession.add(admin)
