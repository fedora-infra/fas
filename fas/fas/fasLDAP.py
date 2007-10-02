# -*- coding: utf-8 -*-
#
# Copyright © 2007  Red Hat, Inc. All rights reserved.
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
# Author(s): Mike McGrath <mmcgrath@redhat.com>
#            Toshio Kuratomi <tkuratom@redhat.com>
#            Ricky Zhou <ricky@fedoraproject.org>
#

'''
python-fedora, python module to interact with Fedora Infrastructure Services
'''

import ldap
from ldap import modlist
import datetime
from random import Random
import sha
from base64 import b64encode
import sys
    

class AuthError(Exception):
    pass

class Server(object):
    def __init__(self, server=None, who=None, password=None):
        ### FIXME: Before deploy, get the default server, user, and password
        # from the fedora-db-access file.
        server = server or 'localhost'
        who = who or 'cn=directory manager'
        password = password or 'test'

        self.ldapConn = ldap.open(server)
        self.ldapConn.simple_bind_s(who, password)

    def add(self, base, attributes):
        ''' Add a new group record to LDAP instance '''
        attributes=[ (k, v) for k,v in attributes.items() ]
        self.ldapConn.add_s(base, attributes)

    def delete(self, base):
        ''' Delete target base '''
        self.ldapConn.delete_s(base)

    def modify(self, base, attribute, new, old=None):
        ''' Modify an attribute, requires write access '''
        if new == None:
            return None
        new = str(new)
        if new == old:
            return None

        #o = { attribute : old }
        #n = { attribute : new }

        ldif = []
        ldif.append((ldap.MOD_DELETE,attribute,None))
        ldif.append((ldap.MOD_ADD,attribute,new))

        #ldif = ldap.modlist.modifyModlist(o, n, ignore_oldexistent=1)
        # commit
        self.ldapConn.modify_s(base, ldif)

    def search(self, base, ldapFilter, attributes=None):
        ''' Basic search function '''
        scope = ldap.SCOPE_SUBTREE
        count = 0
        timeout = 2
        result_set = []
        try:
            result_id = self.ldapConn.search(base, scope, ldapFilter, attributes)
            while True:
                result_type, result_data = self.ldapConn.result(result_id, timeout)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            if len(result_set) == 0:
                return
        except ldap.LDAPError, e:
            raise

        return result_set

###############################################################################
# Group - Contains information about a specific group, 'sysadmin' would be
#         an example of a Group
###############################################################################

class Group(object):
    ''' Group abstraction class '''

    __server = Server()
    __base = 'ou=FedoraGroups,dc=fedoraproject,dc=org'

    def __init__(self, cn, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupType, fedoraGroupNeedsSponsor, fedoraGroupUserCanRemove, fedoraGroupRequires, fedoraGroupJoinMsg):
        self.cn = cn
        self.fedoraGroupDesc = fedoraGroupDesc
        self.fedoraGroupOwner = fedoraGroupOwner
        self.fedoraGroupType = fedoraGroupType
        self.fedoraGroupNeedsSponsor = fedoraGroupNeedsSponsor
        self.fedoraGroupUserCanRemove = fedoraGroupUserCanRemove
        self.fedoraGroupRequires = fedoraGroupRequires
        self.fedoraGroupJoinMsg = fedoraGroupJoinMsg

    def __json__(self):
        return {'cn': self.cn,
                'fedoraGroupDesc': self.fedoraGroupDesc,
                'fedoraGroupOwner': self.fedoraGroupOwner,
                'fedoraGroupType': self.fedoraGroupType,
                'fedoraGroupNeedsSponsor': self.fedoraGroupNeedsSponsor,
                'fedoraGroupUserCanRemove': self.fedoraGroupUserCanRemove,
                'fedoraGroupRequires': self.fedoraGroupRequires,
                'fedoraGroupJoinMsg': self.fedoraGroupJoinMsg
        }

    @classmethod 
    def newGroup(self, cn, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupNeedsSponsor, fedoraGroupUserCanRemove, fedoraGroupRequires, fedoraGroupJoinMsg):
        ''' Create a new group '''
        attributes = { 'cn' : cn,
                    'objectClass' : ('fedoraGroup'),
                    'fedoraGroupDesc' : fedoraGroupDesc,
                    'fedoraGroupOwner' : fedoraGroupOwner,
                    'fedoraGroupType' : '1',
                    'fedoraGroupNeedsSponsor' : fedoraGroupNeedsSponsor,
                    'fedoraGroupUserCanRemove' : fedoraGroupUserCanRemove,
                    'fedoraGroupRequires' : fedoraGroupRequires,
                    'fedoraGroupJoinMsg' : fedoraGroupJoinMsg,
                    }

        self.__server.add('cn=%s,%s' % (cn, self.__base), attributes)
#        attributes = {
#                    'objectClass' : ('organizationalUnit', 'top'),
#                    'ou' : 'FedoraGroups'
#                    }
#        self.__server.add('ou=FedoraGroups,cn=%s,%s' % (cn, self.__base), attributes)
        return 0


###############################################################################
# UserGroup - Determines information about a user in a group, when they joined
#             who their sponsor is and their approval status are examples of 
#             things found in this group
###############################################################################
class UserGroup(object):
    ''' Individual User->Group abstraction class '''
    def __init__(self, fedoraRoleApprovalDate=None, fedoraRoleSponsor=None, cn=None, fedoraRoleCreationDate=None, objectClass=None, fedoraRoleType=None, fedoraRoleStatus='Not a Member', fedoraRoleDomain=None):
        self.fedoraRoleApprovalDate = fedoraRoleApprovalDate
        self.fedoraRoleSponsor = fedoraRoleSponsor
        self.cn = cn
        self.fedoraRoleCreationDate = fedoraRoleCreationDate
        self.objectClass = objectClass
        self.fedoraRoleType = fedoraRoleType
        self.fedoraRoleStatus = fedoraRoleStatus
        self.fedoraRoleDomain = fedoraRoleDomain


###############################################################################
# Groups - Returns actual information in a group.  This class actual queries
#          the LDAP database.
###############################################################################
class Groups(object):
    ''' Class contains group information '''
    __server = Server()

    def __init__(self):
        ### FIXME: I don't think the username should be used this way.
        self.__userName = None

    @classmethod
    def byUserName(self, cn, includeUnapproved=None, unapprovedOnly=None):
        ''' Return list of groups a certain user is in.  Default excludes all non-approved groups'''
        groups = {}
        if includeUnapproved:
            ldapFilter = 'objectClass=FedoraRole'
        elif unapprovedOnly:
            ldapFilter = '(&(!(fedoraRoleStatus=approved)) (objectClass=fedoraRole))'
        else:
            ldapFilter = '(&(fedoraRoleStatus=approved)(objectClass=FedoraRole))'

        base = 'ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % cn
        try:
            groupsDict = self.__server.search(base, ldapFilter)
        except ldap.NO_SUCH_OBJECT:
            return dict()
        if not groupsDict:
            groupsDict = []
        for group in groupsDict:
            cn = group[0][1]['cn'][0]
            groups[cn] = UserGroup(
                fedoraRoleApprovalDate = group[0][1]['fedoraRoleApprovalDate'][0].decode('utf8'),
                fedoraRoleSponsor = group[0][1]['fedoraRoleSponsor'][0].decode('utf8'),
                cn = group[0][1]['cn'][0].decode('utf8'),
                fedoraRoleCreationDate = group[0][1]['fedoraRoleCreationDate'][0].decode('utf8'),
                objectClass = group[0][1]['objectClass'][0].decode('utf8'),
                fedoraRoleType = group[0][1]['fedoraRoleType'][0].decode('utf8'),
                fedoraRoleStatus = group[0][1]['fedoraRoleStatus'][0].decode('utf8'),
                fedoraRoleDomain = group[0][1]['fedoraRoleDomain'][0].decode('utf8'),
                        )
        ### FIXME: userName shouldn't be shared this way
        self.__userName = cn
        return groups
    
    @classmethod
    def groups(self, searchExpression='*', attributes=[]):
        ''' Return a list of available groups '''
        groups = {}
        ldapFilter = 'cn=%s' % (searchExpression)
        base = 'ou=FedoraGroups,dc=fedoraproject,dc=org'
        groupsDict = self.__server.search(base, ldapFilter, attributes)
        if groupsDict:
            for group in groupsDict:
                name = group[0][1]['cn'][0].decode('utf8')
                groups[name] = Group(
                    cn = group[0][1]['cn'][0].decode('utf8'),
                    fedoraGroupDesc = group[0][1]['fedoraGroupDesc'][0].decode('utf8'),
                    fedoraGroupOwner = group[0][1]['fedoraGroupOwner'][0].decode('utf8'),
                    fedoraGroupType = group[0][1]['fedoraGroupType'][0].decode('utf8'),
                    fedoraGroupNeedsSponsor = group[0][1]['fedoraGroupNeedsSponsor'][0].decode('utf8'),
                    fedoraGroupUserCanRemove = group[0][1]['fedoraGroupUserCanRemove'][0].decode('utf8'),
                    fedoraGroupRequires = group[0][1]['fedoraGroupRequires'][0].decode('utf8'),
                    fedoraGroupJoinMsg = group[0][1]['fedoraGroupJoinMsg'][0].decode('utf8'))
        else:
            return None
        return groups

    @classmethod
    def remove(self, groupName, userName=None):
        ''' Remove user from a group '''
        ### FIXME: Should require the userName instead of sharing it this way
        if not userName:
            userName = self.__userName
        try:
            g = self.byUserName(userName, includeUnapproved=True)[groupName]
        except:
            raise TypeError, 'User not in group %s' % groupName
        try:
            self.__server.delete('cn=%s+fedoraRoleType=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (g.cn, g.fedoraRoleType, userName))
        except ldap.NO_SUCH_OBJECT:
            self.__server.delete('cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (g.cn, userName))
        except:
            raise TypeError, 'Could Not delete %s from %s' % (userName, g.cn)

    @classmethod
    def apply(self, groupName, userName=None):
        ''' Apply for a group '''

        if not userName:
            userName = self.__userName

        if groupName in self.byUserName(userName):
            # Probably shouldn't be 'TypeError'
            raise TypeError, 'Already in that group'
        try:
            self.byGroupName(groupName)
        except TypeError:
            raise TypeError, 'Group "%s" does not exist' % groupName

        dt = datetime.datetime.now()
        now = '%.2i-%.2i-%.2i %.2i:%.2i:%.2i.%.2i' % (dt.year,
                                        dt.month,
                                        dt.day,
                                        dt.hour,
                                        dt.minute,
                                        dt.second,
                                        dt.microsecond)

        attributes = { 'cn' : groupName,
                    'fedoraRoleApprovaldate' : 'NotApproved',
                    'fedoraRoleCreationDate' : str(now),
                    'fedoraRoleDomain' : 'None',
                    'fedoraRoleSponsor' : 'None',
                    'fedoraRoleStatus' : 'unapproved',
                    'fedoraRoleType' : 'user',
                    'objectClass' : ('fedoraRole')}
        self.__server.add('cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (groupName, userName), attributes) 


    @classmethod
    def byGroupName(cls, cn, includeUnapproved=None, unapprovedOnly=None):
        ''' List users in a group.  Default does not show unapproved '''
        self = cls()
        users = {}
        if includeUnapproved:
            ldapFilter = 'cn=%s' % cn
        elif unapprovedOnly:
            ldapFilter = '(&(cn=%s) (objectClass=fedoraRole) (!(fedoraRoleStatus=approved)))' % cn
        else:
            ldapFilter = '(&(cn=%s) (objectClass=fedoraRole)  (fedoraRoleStatus=approved))' % cn
        base = 'ou=People,dc=fedoraproject,dc=org'
        attributes = ['cn']
        usersDict = self.__server.search(base, ldapFilter)
        try:
            for user in usersDict:
                userName = user[0][0].split(',')[2].split('=')[1]

                users[userName] = UserGroup(
                    fedoraRoleApprovalDate = user[0][1]['fedoraRoleApprovalDate'][0].decode('utf8'),
                    fedoraRoleSponsor = user[0][1]['fedoraRoleSponsor'][0].decode('utf8'),
                    cn = user[0][1]['cn'][0].decode('utf8'),
                    fedoraRoleCreationDate = user[0][1]['fedoraRoleCreationDate'][0].decode('utf8'),
                    objectClass = user[0][1]['objectClass'][0].decode('utf8'),
                    fedoraRoleType = user[0][1]['fedoraRoleType'][0].decode('utf8'),
                    fedoraRoleStatus = user[0][1]['fedoraRoleStatus'][0].decode('utf8'),
                    fedoraRoleDomain = user[0][1]['fedoraRoleDomain'][0].decode('utf8'),
                )
        except TypeError:
            users = []
        return users

class Person(object):
    '''Information and attributes about users '''
    __base = 'ou=People,dc=fedoraproject,dc=org'
    __server = Server()
    def __init__(self):
        ### FIXME: Not sure what this is used for.  It might be able to go
        # away.  It might need to be made a public attribute.
        self.__filter = ''
   
    @classmethod 
    def newPerson(self, cn, givenName, mail, telephoneNumber, postalAddress):
        ''' Create a new user '''
        dt = datetime.datetime.now()
        now = '%.2i-%.2i-%.2i %.2i:%.2i:%.2i.%.2i' % (dt.year,
                                        dt.month,
                                        dt.day,
                                        dt.hour,
                                        dt.minute,
                                        dt.second,
                                        dt.microsecond)
        attributes = { 'cn' : cn,
                    'objectClass' : ('fedoraPerson', 'inetOrgPerson', 'organizationalPerson', 'person', 'top'),
                    'displayName' : cn,
                    'sn' : cn,
                    'cn' : cn,
                    'fedoraPersonSshKey' : '',
                    'facsimileTelephoneNumber' : '',
                    'fedoraPersonApprovalStatus' : 'approved',
                    'givenName' : givenName,
                    'mail' : mail,
                    'fedoraPersonKeyId' : '',
                    'description' : '',
                    'fedoraPersonCreationDate' : str(now),
                    'telephoneNumber' : telephoneNumber,
                    'fedoraPersonBugzillaMail' : mail,
                    'postalAddress' : postalAddress,
                    'fedoraPersonIrcNick' : '',
                    'userPassword' : 'Disabled'
                    }
        self.__server.add('cn=%s,%s' % (cn, self.__base), attributes)
        attributes = {
                    'objectClass' : ('organizationalUnit', 'top'),
                    'ou' : 'Roles'
                    }
        self.__server.add('ou=Roles,cn=%s,%s' % (cn, self.__base), attributes)
        return 0

    ### FIXME: Overriding __getattr__ and __setattr__ can be tricky and have
    # performance penalties.  If that's okay, you may also want to consider
    # inheriting from dict as that might be a better access method.
    def __getattr__(self, attr):
        if attr == '__filter':
            return self.__filter
        if attr == 'userName':
            attr = 'cn'
        try:
            attributes = []
            attributes.append(attr)
            return self.__server.search(self.__base, self.__filter, attributes)[0][0][1][attr][0].decode('utf8')
        except:
            # Should probably raise here.
            return None

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            #return setattr(self.__class__, attr, value)
            self.__dict__[attr] = value
            return
        base = 'cn=%s,ou=People,dc=fedoraproject,dc=org' % self.__getattr__('cn')

        if self.__getattr__(attr):
            self.__server.modify(base, attr, value, self.__getattr__(attr))
        else:
            try:
                self.__server.modify(base, attr, value)
            except:
                self.__server.modify(base, attr, value, self.__getattr__(attr))

    @classmethod
    def users(self, searchExpression='*', findAttr='cn'):
        ''' Returns a list of users '''
        users = []
        ldapFilter = '(&(objectClass=top)(%s=%s))' % (findAttr, searchExpression)
        attributes = ['cn']
        usersDict = self.__server.search(self.__base, ldapFilter, attributes)
        if usersDict:
            for user in usersDict:
                users.append(user[0][1]['cn'][0].decode('utf8'))
        else:
            return None
        return users

    @classmethod
    def byFilter(cls, ldapFilter):
        ''' Returns only the first result in the search '''
        self = cls()
        self.__filter = ldapFilter
        return self

    @classmethod
    def byUserName(self, cn):
        '''Wrapper for byFilter - search by cn'''
        return self.byFilter('cn=%s' % cn)

    @classmethod
    def auth(self, who, password, ldapServer=None):
        ''' Basic Authentication Module '''
        if not password:
            raise AuthError
        if not ldapServer:
            s = Server()
            ldapServer = s.ldapConn
        who = 'cn=%s,ou=People,dc=fedoraproject,dc=org' % who
        try:
            ldapServer.simple_bind_s(who, password)
        except:
            raise AuthError

    def upgrade(self, group):
        ''' Upgrade user in group '''
        base = 'cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (group, self.cn)
        g = Groups.byGroupName(group, includeUnapproved=True)[self.cn]
        if not g.fedoraRoleStatus.lower() == 'approved':
            '''User not approved or sponsored'''
            raise TypeError, 'User is not approved'
        if g.fedoraRoleType.lower() == 'administrator':
            raise TypeError, 'User cannot be upgraded beyond administrator'
        elif g.fedoraRoleType.lower() == 'sponsor':
            self.__server.modify(base, 'fedoraRoleType', 'administrator', g.fedoraRoleType)
        elif g.fedoraRoleType.lower() == 'user':
            self.__server.modify(base, 'fedoraRoleType', 'sponsor', g.fedoraRoleType)

    def downgrade(self, group):
        ''' Downgrade user in group '''
        base = 'cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (group, self.cn)
        g = Groups.byGroupName(group, includeUnapproved=True)[self.cn]
        if not g.fedoraRoleStatus.lower() == 'approved':
            '''User not approved or sponsored'''
            raise TypeError, 'User is not approved'
        if g.fedoraRoleType.lower() == 'user':
            raise TypeError, 'User cannot be downgraded below user, did you mean remove?'
        elif g.fedoraRoleType.lower() == 'sponsor':
            self.__server.modify(base, 'fedoraRoleType', 'user', g.fedoraRoleType)
        elif g.fedoraRoleType.lower() == 'administrator':
            self.__server.modify(base, 'fedoraRoleType', 'sponsor', g.fedoraRoleType)

    def sponsor(self, groupName, sponsor):
        ''' Sponsor current user '''
        base = 'cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (groupName, self.cn)
        g = Groups.byGroupName(groupName, includeUnapproved=True)[self.cn]
        group = Groups.groups(groupName)[groupName]
        dt = datetime.datetime.now()
        now = '%.2i-%.2i-%.2i %.2i:%.2i:%.2i.%.2i' % (dt.year,
                                        dt.month,
                                        dt.day,
                                        dt.hour,
                                        dt.minute,
                                        dt.second,
                                        dt.microsecond)
        self.__server.modify(base, 'fedoraRoleApprovalDate', now)
        if group.fedoraGroupNeedsSponsor.lower() == 'true':
            self.__server.modify(base, 'fedoraRoleSponsor', sponsor)
        else:
            self.__server.modify(base, 'fedoraRoleSponsor', 'None')
        self.__server.modify(base, 'fedoraRoleStatus', 'approved')

    def generatePassword(self,password=None,length=14,salt=''):
        ''' Generate Password '''
        secret = {} # contains both hash and password

        if not password:
            rand = Random() 
            password = ''
            # Exclude 0,O and l,1
            righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
            lefthand = '789yuiophjknmYUIPHJKLNM'
            for i in range(length):
                if i%2:
                    password = password + rand.choice(lefthand)
                else:
                    password = password + rand.choice(righthand)
        
        ctx = sha.new(password)
        ctx.update(salt)
        secret['hash'] = "{SSHA}%s" % b64encode(ctx.digest() + salt)
        secret['pass'] = password

        return secret


class UserAccount:
    def __init__(self):
        self.realName = ''
        self.userName = ''
        self.primaryEmail = ''
        self.groups = []
