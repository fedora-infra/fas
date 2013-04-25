# -*- coding: utf-8 -*-
from turbogears import identity

# A list of functions to call to get the various entries that
#   should be shown in the sidebar
entryfuncs = []

# Generator that returns each of the entries
def getEntries():
    for f in entryfuncs:
        entries = f()
        for entry in entries:
            yield entry


# Stock entries used by FAS everywhere
def stockentries():
    entries = []
    if not identity.current.anonymous and (
            'sysadmin' in identity.current.groups
            or 'accounts' in identity.current.groups
        ):
        entries.append((_('New Group'), '/group/new', 'icon-plus-sign'))
        entries.append((_('Users'), '/user/list', 'icon-group'))
    if not identity.current.anonymous:
        entries.append((_('Groups'), '/group/list/A*', 'icon-comments-alt'))
        entries.append((_('Log Out'), '/logout', 'icon-signout'))
    return entries

entryfuncs.append(stockentries)
