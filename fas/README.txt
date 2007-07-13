fas

This is a TurboGears (http://www.turbogears.org) project. It can be
started by running the start-fas.py script.


LDAP Dump / restore:
ldapsearch -x -D 'cn=directory manager' -b 'dc=fedoraproject,dc=org' "objectclass=*" \* aci > LDAPDump
ldapadd -x -D 'cn=directory manager' -f LDAPDump -W


Add to top of LDIF if pulling from Postgres:
# fedoraproject.org
dn: dc=fedoraproject,dc=org
objectClass: top
objectClass: domain
dc: fedoraproject
aci: (targetattr!="userPassword")(version 3.0; acl "Enable anonymous access";a
 llow (read, search, compare)userdn="ldap:///anyone";)
aci: (targetattr="carLicense ||description ||displayName ||facsimileTelephoneN
 umber ||homePhone ||homePostalAddress ||initials ||jpegPhoto ||labeledURL ||m
 ail ||mobile ||pager ||photo ||postOfficeBox ||postalAddress ||postalCode ||p
 referredDeliveryMethod ||preferredLanguage ||registeredAddress ||roomNumber |
 |secretary ||seeAlso ||st ||street ||telephoneNumber ||telexNumber ||title ||
 userCertificate ||userPassword ||userSMIMECertificate ||x500UniqueIdentifier"
 )(version 3.0; acl "Enable self write for common attributes"; allow (write) u
 serdn="ldap:///self";)

# FedoraGroups, fedoraproject.org
dn: ou=FedoraGroups, dc=fedoraproject,dc=org
objectClass: top
objectClass: organizationalunit
ou: FedoraGroups

# People, fedoraproject.org
dn: ou=People, dc=fedoraproject,dc=org
objectClass: top
objectClass: organizationalunit
ou: People

