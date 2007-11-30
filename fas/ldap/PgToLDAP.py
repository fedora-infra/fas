#!/usr/bin/env python

"""
  PgToLDAP is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  PgToLDAP is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with PgToLDAP; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

  Id: $Id: PgToLDAP.py,v 1.5 2006/12/07 01:40:06 lyz Exp $
"""

import sys, time
import ldap, ldif, pgdb, ldap.modlist
from optparse import OptionParser
import sha
import base64
from random import randrange


version = "0.112"

def encode_SSHA_password ( password ):
     p_ssha = sha.new( password )
     salt = ''

     for n in range(7):
        salt += chr(randrange(256))


     p_ssha.update( salt )
     p_ssha_base64 = base64.encodestring(p_ssha.digest() + salt + '' )
     return '%s%s' %( '{SSHA}', p_ssha_base64 )



def parseArgs():
    parser = OptionParser(version="%prog " + version)
    parser.add_option ("-v", "--verbose", dest="verbose", action="store_true", default=False,
                       help="Verbose output")

    parser.add_option ("--pgUser", dest="pgUser", default="postgres",
                       help="PostgreSQL User [default: %default]", metavar="USER")
    parser.add_option ("--pgPassword", dest="pgPassword", 
                       help="PostgreSQL Password", metavar="PASSWORD")
    parser.add_option ("--pgHost", dest="pgHost", default="localhost",
                       help="PostgreSQL Host [default: %default]", metavar="HOST")
    parser.add_option ("--pgPort", dest="pgPort", default="5432",
                       help="PostgreSQL Port [default: %default]", metavar="PORT")
    parser.add_option ("--pgDb", dest="pgDB", 
                       help="PostgreSQL Database", metavar="DATABASE")

    parser.add_option ("-o", "--output", dest="outType", default="file",
                       help="Output Type [file|ldap] [default: %default]")
    parser.add_option ("-f", "--file", dest="outFile", default="out.ldif",
                       help="Output file [default: %default]", metavar="FILE")

    parser.add_option ("--ldapUser", dest="ldapUser", default="cn=Directory Manager",
                       help="LDAP User [default: %default]", metavar="USER")
    parser.add_option ("--ldapPassword", dest="ldapPassword", 
                       help="LDAP Password", metavar="PASSWORD")
    parser.add_option ("--ldapHost", dest="ldapHost", default="localhost",
                       help="LDAP Host [default: %default]", metavar="HOST")
    parser.add_option ("--ldapPort", dest="ldapPort", default="389",
                       help="LDAP Port [default: %default]", metavar="PORT")
    parser.add_option ("--ldapOU", dest="ldapBaseOU", default="dc=fedoraproject, dc=org",
                       help="LDAP Base OU [default: %default]", )
    (options, args) = parser.parse_args()
    if options.outType != "file" and options.outType != "ldap":
        parser.error("Output type must be file or ldap")
    return (options, args)

def connPostgres(user, password, db, host, port):
    """Tries to connect to the Postgres db server.
    Will exit with exit code 1 it it fails."""
    global verbose
    if verbose:
        print "Connecting to postgres://%s@%s:%s" % (user, host, port)
    try:
        dbConn = pgdb.connect(user=user,
                              password=password,
                              database=db,
                              host='%s:%s' %(host, port))
        return dbConn
    except:
        print "Error connecting to Postgres server"
        # TODO: Remove exit comment
        sys.exit(1)

def connLDAP(user, password, host, port):
    """Tries to bind to the LDAP server.
    Will exit with exit code 1 it it fails."""
    global verbose
    if verbose:
        print "Connecting to ldap://%s@%s:%s" % (user, host, port)
    try:
        ldapConn = ldap.open(host)
        ldapConn.protocol_version = ldap.VERSION3
        ldapConn.simple_bind_s(user, password)
        return ldapConn
    except ldap.LDAPError, error_message:
        print 'Error connecting to LDAP Server'
        print error_message
        sys.exit(1)

def openLdifFile(filename):
    """Tries to open the output file for writing.
    Will exit with exit code 1 it it fails."""
    global verbose
    if verbose:
        print "Opening output file %s" % filename
    try:
        #ldifWriter = ldif.LDIFWriter(ldap.initialize('ldap://localhost:1390'),filename)
        fileHandel = open (filename,'w')

       #  |  __init__(self, output_file, base64_attrs=None, cols=76, line_sep='\n')
    #  |      output_file
    #  |          file object for output
    #  |      base64_attrs
    #  |          list of attribute types to be base64-encoded in any case
    #  |      cols
       #  |          Specifies how many columns a line may have before it's
        #  |          folded into many lines.
    #  |      line_sep
    #  |          String used as line separator



        ldifWriter = ldif.LDIFWriter(fileHandel,"None")
        return ldifWriter
    except ldap.LDAPError, error_message:
        print "Error opening output file: %s" % (filename)
        print error_message
        sys.exit(1)

def cleanLDAP(ldapConn, ldapBaseOU):
    """Removes all existing entries under ou=People and ou=Groups for
    the defined base OU.
    Will exit with exit code 1 if an LDAP error is encountered."""
    global verbose
    if verbose:
        print "Deleting existing users from LDAP"
    try:
        timeout = 0
        result_id = ldapConn.search("ou=People, " + ldapBaseOU, 
                                 ldap.SCOPE_ONELEVEL,
                                 "cn=*",
                                 None)
        while 1:
            result_type, result_data = ldapConn.result(result_id, timeout)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    if verbose:
                        print "Deleting LDAP user: " + result_data[0][1]['cn'][0]
                    ldapConn.delete_s(result_data[0][0])
    except ldap.LDAPError, error_message:
        print "Error deleting existing users from LDAP"
        print error_message
        sys.exit(1)

    if verbose:
        print "Deleting existing groups from LDAP"
    try:
        timeout = 0
        result_id = ldapConn.search("ou=Groups, " + ldapBaseOU, 
                                 ldap.SCOPE_ONELEVEL,
                                 "cn=*",
                                 None)
        while 1:
            result_type, result_data = ldapConn.result(result_id, timeout)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    if verbose:
                        print "Deleting LDAP group: " + result_data[0][1]['cn'][0]
                    ldapConn.delete_s(result_data[0][0])
    except ldap.LDAPError, error_message:
        print "Error deleting existing groups from LDAP"
        print error_message
        sys.exit(1)

def main():
    global verbose
    (options, cruft) = parseArgs()
    verbose = options.verbose

    dbConn = connPostgres(options.pgUser, options.pgPassword,
                          options.pgDB, options.pgHost, options.pgPort)

    # Cleanup LDAP (if necessary)
    if options.outType == "ldap":
        ldapConn = connLDAP(options.ldapUser, options.ldapPassword,
                            options.ldapHost, options.ldapPort)
        #cleanLDAP(ldapConn, options.ldapBaseOU)
    else:
        ldifWriter = openLdifFile(options.outFile)

    # Copy all users from db to ldap/ldif
    # this will to queries and mappings
    
    try:
        if verbose:
            print "Selecting all users from Postgres Database"
        userCursor = dbConn.cursor()
        userCursor.execute ("SELECT * FROM person")

    #id, username, email 2, human_name 3, gpg_keyid 4, ssh_key 5, password 6, comments 7,  postal_address 8, telephone 9, facsimile 10, affiliation 11, creation 12, approval_status 13, internal_comments 14, wiki_prefs 15, ircnick 16
    except:
        print "Error selecting users from db"
        raise
        sys.exit(1)
    while 1:
        user = userCursor.fetchone()
        if user == None:
            break

        date = str(user[12]).split('.')[0]
        timestamp = time.strftime('%s', time.strptime(date, "%Y-%m-%d %H:%M:%S"))

        # TODO: Create method createLdapUserEntry(user)
        #(dn, entry) = createLdapUserEntry(user)
        if options.outType == "ldif":
            ldifWriter.unparse(dn, entry)
        else:
        

            print "Adding ldif info for " + user[3] + "."

        #userLdif = [["objectClass",["fedoraPerson","organizationalUnit"]] , [ "displayName",[ user[1] ] ] ] 
        userLdif = [["objectClass",["fedoraPerson"]] , [ "displayName",[ user[1] ] ] ] 
        userLdif.append(["mail",[str(user[2])]])
        userLdif.append(["sn",[str(user[1])]])
        userLdif.append(["fedoraPersonBugzillaMail",[str(user[2])]])
        userLdif.append(["cn",[str(user[1])]])
        userLdif.append(["givenName",[str(user[3])]])
        userLdif.append(["fedoraPersonKeyId",[str(user[4])]])
        userLdif.append(["fedoraPersonCertSerial",['-1']])
        userLdif.append(["fedoraPersonSshKey",[str(user[5])]])
        userLdif.append(["userPassword",[encode_SSHA_password(str(user[6]))]])
        userLdif.append(["postalAddress",[str(user[8])]])
        userLdif.append(["telephoneNumber",[str(user[9])]])
        userLdif.append(["fax",[str(user[10]) or "None"]])
        userLdif.append(["o",[str(user[11]) or "None" ]]) # affiliation is set to the o -- another stretch ??
        userLdif.append(["fedoraPersonCreationDate",[str(timestamp)]])
        userLdif.append(["fedoraPersonApprovalStatus",[str(user[13])]])
        userLdif.append(["description",[str(user[14])]]) #this one may be a streach -- original field was internal comments
        userLdif.append(["fedoraPersonIrcNick",[str(user[16])]])
        #userLdif.append(["ou",["Roles"]]) Adding an OU instead
       
        print userLdif
        #for userKey in userLdif.keys():
        #print "Key Name -> " + userKey 
        #print ":::Key Value::: " 
        #print userLdif[userKey]
        #ldifWriter.unparse("dc=fedoraproject,dc=org cn=" + user[3] , { userKey : [str(userLdif[userKey])] } )

        #print userLdif.keys()
        #print userLdif.values()
        ldifWriter.unparse("cn=" + str(user[1]) +",ou=People,dc=fedoraproject,dc=org" , userLdif )

        roleOuLdif = [["objectClass",["organizationalUnit"]] , [ "ou",[ "Roles" ] ] ] 
        ldifWriter.unparse("ou=Roles,cn=" + str(user[1]) +",ou=People,dc=fedoraproject,dc=org" , roleOuLdif )        

        #ldifWriter.unparse("dc=fedoraproject,dc=org, cn=" + user[3] , [ ['ano',['domini']],['uances',['od']] ])

        #time.sleep (2)
    
                
            #ldapConn.add_s(dn, entry)

    userCursor.close()

    
    
    # Select all groups from the DB
    
    try:
        if verbose:
            print "Selecting all groups from Postgres Database"
        groupCursor = dbConn.cursor()
        groupCursor.execute ("SELECT * FROM project_group")



    except:
        print "Error selecting groups from db"
        raise
        sys.exit(1)
    while 1:
        group = groupCursor.fetchone()
        if group == None:
            break
        # TODO: Create method createLdapGroupEntry(group)
        #(dn, entry) = createLdapGroupEntry(group)
        if options.outType == "ldif":
            ldifWriter.unparse(dn, entry)
        else:
            #ldapConn.add_s(dn, entry)
        
            print "Adding group info for %s." % group[7]
            #id0, owner_id1, group_type2, needs_sponsor3, user_can_remove4, prerequisite_id5, joinmsg6, name7

            uidLookupCursor = dbConn.cursor()
            uidLookupCursor.execute ("SELECT username FROM person where id =" + str(group[1]) )
            owner = uidLookupCursor.fetchone()
            if str(group[5]) != "None" :
                uidLookupCursor.execute ("SELECT name FROM project_group where id =" + str(group[5]) )
                prereq = uidLookupCursor.fetchone()
                print prereq
            else:
                prereq=["None"]

        print owner

            #id0, name1, owner_id2, group_type3, needs_sponsor4, user_can_remove5, prerequisite_id6, joinmsg7
        userLdif = [["objectClass",["fedoraGroup"]] ] 
        userLdif.append(["cn",[str(group[7])]])
        userLdif.append(["fedoraGroupOwner",owner]) # need to get a cn for this not just the id
        #userLdif.append(["groupOwner",[str(group[2])]]) # need to get a cn for this not just the id
        userLdif.append(["fedoraGroupType",[str(group[3]) or "None" ]])

        #we're using the boolean type for these.  This means they need to be converted to the TRUE and FALSE strings

        if str(group[3]) == "0" :
            group[3]="FALSE"
        else:
            group[3]="TRUE"

        if str(group[4]) == "0" :
            group[4]="FALSE"
        else:
            group[4]="TRUE"

        if group[5] == None:
            group[5] = ""
        
        userLdif.append(["fedoraGroupNeedsSponsor",[str(group[3])]]) #need to convert to bool
        userLdif.append(["fedoraGroupUserCanRemove",[str(group[4])]]) #need to convert to bool
        userLdif.append(["fedoraGroupDesc",[str('Please fill out a Group Description')]]) #need to convert to bool
        #userLdif.append(["groupPrerequisite",[str(group[5])]])
        userLdif.append(["fedoraGroupRequires",[str(group[5])]]) # <- Hope this is added properly - Ricky
        #userLdif.append(["groupPrerequisite",prereq]) not currently in the schema
        userLdif.append(["fedoraGroupJoinMsg",[str(group[6]) or "None" ]])
        ldifWriter.unparse("cn=" + str(group[7]) +",ou=FedoraGroups,dc=fedoraproject,dc=org" , userLdif )


    groupCursor.close()        
    
    # Select all roles from the DB
    
    try:
        if verbose:
            print "Selecting all roles from Postgres Database"
        roleCursor = dbConn.cursor()
        roleCursor.execute ("SELECT * FROM role")
    #person_id, project_group_id, role_type, role_domain, role_status, internal_comments, sponsor_id (Points to a person), creation (TIMESTAMP), approval (TIMESTAMP)
    except:
        print "Error selecting roles from db"
        raise
        sys.exit(1)        
    while 1:
        role = roleCursor.fetchone()
        if role == None:
            break
        date1 = str(role[7]).split('.')[0]
        date2 = str(role[8]).split('.')[0]
        try:
            timestamp1 = time.strftime('%s', time.strptime(date1, "%Y-%m-%d %H:%M:%S"))
        except:
            timestamp1 = "None"
        try:
            timestamp2 = time.strftime('%s', time.strptime(date2, "%Y-%m-%d %H:%M:%S"))
        except:
            timestamp2 = "None"
        # TODO: Create method createLdapRoleEntry(group)
        #(dn, entry) = createLdapGroupRole(group)
        if options.outType == "ldif":
            ldifWriter.unparse(dn, entry)
        else:
            #ldapConn.add_s(dn, entry)
            #person_id0, group_project_id1, role_type2, role_domain3, role_status4, internal_comments5, sponsor_id6, creation7, approval8


            uidRoleCursor = dbConn.cursor()
            uidRoleCursor.execute ("SELECT username FROM person where id =" + str(role[0]) )
            username = uidRoleCursor.fetchone()
            uidRoleCursor.execute ("SELECT name FROM project_group where id =" + str(role[1]) )
            group = uidRoleCursor.fetchone()
            if str(role[6]) != "None" :
                uidRoleCursor.execute ("SELECT username FROM person where id =" + str(role[6]) )
                sponsor = uidRoleCursor.fetchone()
            else:
                sponsor = ["None"]

            print "Adding " + str(role[4]) + " role info for " + group[0] + " for user " + username[0] + "."
            #if str(group[6]) != "None" :
            #    uidLookupCursor.execute ("SELECT name FROM project_group where id =" + str(group[6]) )
        #    prereq = uidLookupCursor.fetchone()
            #    print prereq
        #else:
        #    prereq=["None"]
        #print owner 

  #person_id0, group_project_id1, role_type2, role_domain3, role_status4, internal_comments5, sponsor_id6, creation7, approval8

        roleLdif = [["objectClass",["fedoraRole"]] ] 
        #roleLdif.append(["cn",[str(group[0]) + str(role[2])]]) #Fix me
        roleLdif.append(["cn",[str(group[0])]]) #Fix me
        roleLdif.append(["fedoraRoleType",[str(role[2])]])
        roleLdif.append(["fedoraRoleDomain",[str(role[3]) or "None" ]])
        roleLdif.append(["fedoraRoleStatus",[str(role[4])]])
        roleLdif.append(["fedoraRoleSponsor",sponsor])
        roleLdif.append(["fedoraRoleCreationDate",[str(timestamp1)]])
        roleLdif.append(["fedoraRoleApprovalDate",[str(timestamp2)]])

        ldifWriter.unparse("cn=" + group[0] + ",ou=Roles,cn=" + username[0] + ",ou=People,dc=fedoraproject,dc=org" , roleLdif )

    roleCursor.close()
      
    sys.exit(1)    
if __name__ == "__main__":
    main()
