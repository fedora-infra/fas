fas

This is a TurboGears (http://www.turbogears.org) project. It can be
started by running the start-fas.py script.


LDAP Dump / restore:
ldapsearch -x -D 'cn=directory manager' -b 'dc=fedoraproject,dc=org' "objectclass=*" \* aci > LDAPDump
ldapadd -x -D 'cn=directory manager' -f LDAPDump -W
