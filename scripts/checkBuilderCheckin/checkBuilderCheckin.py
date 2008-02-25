#!/usr/bin/python

import urllib
import koji
import socket
import datetime
import time

FIVE_MIN = 300
FIFTEEN_MIN = 900

k = koji.ClientSession('https://koji.fedoraproject.org/kojihub', {})
hosts = k.listHosts()

me = socket.gethostname()
me = 'ppc3'
#k.getLastHostUpdate
for host in hosts:
    if host['name'].startswith(me):
        t = k.getLastHostUpdate(host['id'])
        dt = time.strptime(t.split('.')[0], "%Y-%m-%d %H:%M:%S")

        print time.time() - time.mktime(dt)
        
        if host['ready'] == False and host['task_load'] >= host['capacity']:
            print "restarting"

