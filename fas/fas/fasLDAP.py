#!/usr/bin/python

import ldap

class Server:
    def __init__(self, server='localhost', who='', password=''):
        self.ldapConn = ldap.open(server)
        self.ldapConn.simple_bind_s(who, password)


###############################################################################
# Group - Contains information about a specific group, 'sysadmin' would be
#         an example of a Group
###############################################################################

class Group:
    ''' Group abstraction class '''
    __base = 'ou=FedoraGroups,dc=fedoraproject,dc=org'
    __server = Server()
    __filter = ''
    __cn = ''

    def __init__(self, cn, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupType, fedoraGroupNeedsSponsor, fedoraGroupUserCanRemove, fedoraGroupJoinMsg):
        self.cn = cn
        self.fedoraGroupDesc = fedoraGroupDesc
        self.fedoraGroupOwner = fedoraGroupOwner
        self.fedoraGroupType = fedoraGroupType
        self.fedoraGroupNeedsSponsor = fedoraGroupNeedsSponsor
        self.fedoraGroupUserCanRemove = fedoraGroupUserCanRemove
        self.fedoraGroupJoinMsg = fedoraGroupJoinMsg

#    def __getattr__(self, attr):
#        if attr.startswith('_'):
#            print 'GET %s=%s' % (attr, self.__getattr__(attr))
#            if attr == '__filter':
#                return self.__filter
#        if attr == 'userName':
#            return self.__getattr__('cn')
#        try:
#            attributes = []
#            attributes.append(attr)
#            return search(self.__base, self.__filter, attributes)[0][0][1][attr][0]
#        except:
#            # Should probably raise here.
#            return None
#
#    def __setattr__(self, attr, value):
#        if attr.startswith('_'):
#            #return setattr(self.__class__, attr, value)
#            self.__dict__[attr] = value
#            return
#        base = 'cn=%s,ou=FedoraGroups,dc=fedoraproject,dc=org' % self.__getattr__('cn')
#
#        if self.__getattr__(attr):
#            modify(base, attr, value, self.__getattr__(attr))
#        else:
#            try:
#                modify(base, attr, value)
#            except:
#                modify(base, attr, value, self.__getattr__(attr))

    @classmethod 
    def newGroup(self, cn, fedoraGroupDesc, fedoraGroupOwner, fedoraGroupNeedsSponsor, fedoraGroupUserCanRemove, fedoraGroupJoinMsg):
        ''' Create a new group '''
        attributes = { 'cn' : cn,
                    'objectClass' : ('fedoraGroup'),
                    'fedoraGroupDesc' : fedoraGroupDesc,
                    'fedoraGroupOwner' : fedoraGroupOwner,
                    'fedoraGroupType' : '1',
                    'fedoraGroupNeedsSponsor' : fedoraGroupNeedsSponsor,
                    'fedoraGroupUserCanRemove' : fedoraGroupUserCanRemove,
                    'fedoraGroupJoinMsg' : fedoraGroupJoinMsg,
                    }
        add('cn=%s,%s' % (cn, self.__base), attributes)
#        attributes = {
#                    'objectClass' : ('organizationalUnit', 'top'),
#                    'ou' : 'FedoraGroups'
#                    }
#        add('ou=FedoraGroups,cn=%s,%s' % (cn, self.__base), attributes)
        return 0


###############################################################################
# UserGroup - Determines information about a user in a group, when they joined
#             who their sponsor is and their approval status are examples of 
#             things found in this group
###############################################################################
class UserGroup:
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
class Groups:
    ''' Class contains group information '''
    __userName = None

    @classmethod
    def byUserName(self, cn, includeUnapproved=None, unapprovedOnly=None):
        ''' Return list of groups a certain user is in.  Default excludes all non-approved groups'''
        server = Server()
        groups = {}
        if includeUnapproved:
            filter = 'objectClass=FedoraRole'
        elif unapprovedOnly:
            filter = '(&(!(fedoraRoleStatus=approved)) (objectClass=fedoraRole))'
        else:
            filter = '(&(fedoraRoleStatus=approved)(objectClass=FedoraRole))'

        base = 'ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % cn
        try:
            groupsDict = search(base, filter)
        except ldap.NO_SUCH_OBJECT:
            return dict()
        if not groupsDict:
            groupsDict = []
        for group in groupsDict:
            cn = group[0][1]['cn'][0]
            groups[cn] = UserGroup(
                fedoraRoleApprovalDate = group[0][1]['fedoraRoleApprovalDate'][0],
                fedoraRoleSponsor = group[0][1]['fedoraRoleSponsor'][0],
                cn = group[0][1]['cn'][0],
                fedoraRoleCreationDate = group[0][1]['fedoraRoleCreationDate'][0],
                objectClass = group[0][1]['objectClass'][0],
                fedoraRoleType = group[0][1]['fedoraRoleType'][0],
                fedoraRoleStatus = group[0][1]['fedoraRoleStatus'][0],
                fedoraRoleDomain = group[0][1]['fedoraRoleDomain'][0]
                        )
        self.__userName = cn
        return groups
    
    @classmethod
    def groups(self, searchExpression='*', attributes=[]):
        ''' Return a list of available groups '''
        groups = {}
        filter = 'cn=%s' % (searchExpression)
        base = 'ou=FedoraGroups,dc=fedoraproject,dc=org'
        groupsDict = search(base, filter, attributes)
        if groupsDict:
            for group in groupsDict:
                name = group[0][1]['cn'][0]
                print group
                groups[name] = Group(
                    cn = group[0][1]['cn'][0],
                    fedoraGroupDesc = group[0][1]['fedoraGroupDesc'][0],
                    fedoraGroupOwner = group[0][1]['fedoraGroupOwner'][0],
                    fedoraGroupType = group[0][1]['fedoraGroupType'][0],
                    fedoraGroupNeedsSponsor = group[0][1]['fedoraGroupNeedsSponsor'][0],
                    fedoraGroupUserCanRemove = group[0][1]['fedoraGroupUserCanRemove'][0],
                    fedoraGroupJoinMsg = group[0][1]['fedoraGroupJoinMsg'][0])
        else:
            return None
        return groups

    @classmethod
    def remove(self, groupName, userName=None):
        ''' Remove user from a group '''
        if not userName:
            userName = self.__userName
        print "userName: %s" % userName
        try:
            g = self.byUserName(userName, includeUnapproved=True)[groupName]
        except:
            raise TypeError, 'User not in group %s' % groupName
        try:
            delete('cn=%s+fedoraRoleType=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (g.cn, g.fedoraRoleType, userName))
        except ldap.NO_SUCH_OBJECT:
            delete('cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (g.cn, userName))
        except:
            raise TypeError, 'Could Not delete %s from %s' % (userName, g.cn)

    @classmethod
    def apply(self, groupName, userName=None):
        ''' Apply for a group '''
        import datetime

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

        attributes = { 'cn' : groupName.encode('utf8'),
                    'fedoraRoleApprovaldate' : 'NotApproved',
                    'fedoraRoleCreationDate' : now,
                    'fedoraRoleDomain' : 'None',
                    'fedoraRoleSponsor' : 'None',
                    'fedoraRoleStatus' : 'unapproved',
                    'fedoraRoleType' : 'user',
                    'objectClass' : ('fedoraRole')}
        add('cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (groupName, userName), attributes) 


    @classmethod
    def byGroupName(cls, cn, includeUnapproved=None, unapprovedOnly=None):
        ''' List users in a group.  Default does not show unapproved '''
        self = cls()
        server = Server()
        users = {}
        if includeUnapproved:
            filter = 'cn=%s' % cn
        elif unapprovedOnly:
            filter = '(&(cn=%s) (objectClass=fedoraRole) (!(fedoraRoleStatus=approved)))' % cn
        else:
            filter = '(&(cn=%s) (objectClass=fedoraRole)  (fedoraRoleStatus=approved))' % cn
        base = 'ou=People,dc=fedoraproject,dc=org'
        self.__attributes = ['cn']
        attributes = ['cn']
        usersDict = search(base, filter)
        try:
            for user in usersDict:
                userName = user[0][0].split(',')[2].split('=')[1]

                users[userName] = UserGroup(
                    fedoraRoleApprovalDate = user[0][1]['fedoraRoleApprovalDate'][0],
                    fedoraRoleSponsor = user[0][1]['fedoraRoleSponsor'][0],
                    cn = user[0][1]['cn'][0],
                    fedoraRoleCreationDate = user[0][1]['fedoraRoleCreationDate'][0],
                    objectClass = user[0][1]['objectClass'][0],
                    fedoraRoleType = user[0][1]['fedoraRoleType'][0],
                    fedoraRoleStatus = user[0][1]['fedoraRoleStatus'][0],
                    fedoraRoleDomain = user[0][1]['fedoraRoleDomain'][0]
                )
        except TypeError:
            users = []
        return users

class Person:
    ''' information and attributes about users '''
    __base = 'ou=People,dc=fedoraproject,dc=org'
    __server = Server()
    __filter = ''
    __cn = ''
   
    @classmethod 
    def newPerson(self, cn, givenName, mail, telephoneNumber, postalAddress):
        ''' Create a new user '''
        import datetime
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
                    'fedoraPersonCreationDate' : now,
                    'telephoneNumber' : telephoneNumber,
                    'fedoraPersonBugzillaMail' : mail,
                    'postalAddress' : postalAddress,
                    'fedoraPersonIrcNick' : '',
                    'userPassword' : 'Disabled'
                    }
        add('cn=%s,%s' % (cn, self.__base), attributes)
        attributes = {
                    'objectClass' : ('organizationalUnit', 'top'),
                    'ou' : 'Roles'
                    }
        add('ou=Roles,cn=%s,%s' % (cn, self.__base), attributes)
        return 0

    def __getattr__(self, attr):
        if attr.startswith('_'):
            print 'GET %s=%s' % (attr, self.__getattr__(attr))
            if attr == '__filter':
                return self.__filter
        if attr == 'userName':
            return self.__getattr__('cn')
        try:
            attributes = []
            attributes.append(attr)
            return search(self.__base, self.__filter, attributes)[0][0][1][attr][0]
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
            modify(base, attr, value, self.__getattr__(attr))
        else:
            try:
                modify(base, attr, value)
            except:
                modify(base, attr, value, self.__getattr__(attr))

    @classmethod
    def users(self, searchExpression='*', findAttr='cn'):
        ''' Returns a list of users '''
        users = []
        filter = '(&(objectClass=top)(%s=%s))' % (findAttr, searchExpression)
        attributes = ['cn']
        usersDict = search(self.__base, filter, attributes)
        if usersDict:
            for user in usersDict:
                users.append(user[0][1]['cn'][0])
        else:
            return None
        return users

    @classmethod
    def byFilter(cls, filter):
        ''' Returns only the first result in the search '''
        self = cls()
        self.__filter = filter
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
        ldapServer.simple_bind_s(who, password)

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
            modify(base, 'fedoraRoleType', 'administrator', g.fedoraRoleType)
        elif g.fedoraRoleType.lower() == 'user':
            modify(base, 'fedoraRoleType', 'sponsor', g.fedoraRoleType)

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
            modify(base, 'fedoraRoleType', 'user', g.fedoraRoleType)
        elif g.fedoraRoleType.lower() == 'administrator':
            modify(base, 'fedoraRoleType', 'sponsor', g.fedoraRoleType)

    def sponsor(self, groupName, sponsor):
        ''' Sponsor current user '''
        import datetime
        base = 'cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (groupName, self.cn)
        g = Groups.byGroupName(groupName, includeUnapproved=True)[self.cn]
        group = Groups.groups(groupName)[groupName]
        print "SPONSORING: %s from %s for %s - %s" % (self.cn, sponsor, groupName, base)
        dt = datetime.datetime.now()
        now = '%.2i-%.2i-%.2i %.2i:%.2i:%.2i.%.2i' % (dt.year,
                                        dt.month,
                                        dt.day,
                                        dt.hour,
                                        dt.minute,
                                        dt.second,
                                        dt.microsecond)
        modify(base, 'fedoraRoleApprovalDate', now)
        if group.fedoraGroupNeedsSponsor.lower() == 'true':
            modify(base, 'fedoraRoleSponsor', sponsor)
        else:
            modify(base, 'fedoraRoleSponsor', 'None')
        modify(base, 'fedoraRoleStatus', 'approved')

    def generatePassword(self,password=None,length=14,salt=''):
        ''' Generate Password '''
        from random import Random
        import sha
        import sha
        from base64 import b64encode
        import sys
    
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

def delete(base, ldapServer=None):
    ''' Delete target base '''
    if not ldapServer:
        s = Server()
        ldapServer = s.ldapConn

    ldapServer.simple_bind_s('cn=directory manager', 'fedoraproject')
    print "Deleteing %s " % base
    ldapServer.delete_s(base)

def add(base, attributes, ldapServer=None):
    ''' Add a new record to LDAP instance '''
    if not ldapServer:
        s = Server()
        ldapServer = s.ldapConn
    attributes=[ (k,v) for k,v in attributes.items() ]

    ldapServer.simple_bind_s('cn=directory manager', 'fedoraproject')
    ldapServer.add_s(base, attributes)

def modify(base, attribute, new, old=None, ldapServer=None):
    ''' Modify an attribute, requires write access '''
    if old == new:
        return None

    if not ldapServer:
        s = Server()
        ldapServer = s.ldapConn

    from ldap import modlist
    ldapServer.simple_bind_s('cn=directory manager', 'fedoraproject')

    if old == None:
        old = 'None'

    if old == new:
        return None

    o = { attribute : old }
    n = { attribute : new }
    ldif = modlist.modifyModlist(o, n)

    #commit
    ldapServer.modify_s(base, ldif)
    ldapServer.unbind_s()

def search(base, filter, attributes=None, ldapServer=None):
    ''' Basic search function '''
    if not ldapServer:
            s = Server()
            ldapServer = s.ldapConn
    scope = ldap.SCOPE_SUBTREE
    count = 0
    timeout = 2
    ldapServer.simple_bind_s('cn=directory manager', 'fedoraproject')
    result_set = []
    try:
        result_id = ldapServer.search(base, scope, filter, attributes)
        while 1:
            result_type, result_data = ldapServer.result(result_id, timeout)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        if len(result_set) == 0:
            print "No results."
            return
    except ldap.LDAPError, e:
        print "Crap: %s" % e
        raise
    ldapServer.unbind_s()

    return result_set
