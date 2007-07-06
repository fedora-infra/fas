from fasLDAP import add, Groups, delete

attributes = { 'cn' : 'infrastructureTest',
                    'fedoraRoleApprovaldate' : 'None',
                    'fedoraRoleCreationDate' : 'None',
                    'fedoraRoleDomain' : 'None',
                    'fedoraRoleSponsor' : 'None',
                    'fedoraRoleStatus' : 'unapproved',
                    'fedoraRoleType' : 'user',
                    'objectClass' : ('fedoraRole')}
print "add('cn=infrastructureTest,ou=Roles,cn=mmcgrath,ou=People,dc=fedoraproject,dc=org', attributes)"
print "delete('cn=infrastructureTest,ou=Roles,cn=mmcgrath,ou=People,dc=fedoraproject,dc=org')"

