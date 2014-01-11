USERS = {'admin':'admin',
          'viewer':'viewer'}
GROUPS = {'admin':['group:admin']}

def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])
