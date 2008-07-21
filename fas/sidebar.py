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
        entries.append(('New Group', '/group/new'))
        entries.append(('User List', '/user/list'))
    if not identity.current.anonymous:
        entries.append(('Group List', '/group/list/A*'))
        entries.append(('Join a Group', '/group/list/A*'))
    return entries

entryfuncs.append(stockentries)
