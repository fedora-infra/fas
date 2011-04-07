
# File Start
WSGISocketPrefix run/wsgi

# Repress TG's stdoutput
WSGIRestrictStdout On

# TG implements its own signal handler.
WSGIRestrictSignal Off

# These are the real tunables
#WSGIDaemonProcess daemon processes=2 threads=2 maximum-requests=1000 user=fas group=fas display-name=fas inactivity-timeout=30
WSGIDaemonProcess fas  processes=2 threads=2 maximum-requests=1000 user=fas display-name=fas inactivity-timeout=30
WSGIPythonOptimize 1

WSGIScriptAlias /accounts /usr/sbin/fas.wsgi/accounts

<Location /accounts>
    WSGIProcessGroup fas
    Order deny,allow
    Allow from all
</Location>

