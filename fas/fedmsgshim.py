""" This is a temporary shim that allows fedmsg to be an optional dependency of
fas.  If fedmsg is installed, these function calls will try to actually send
messages.  If it is not installed, it will return silently.

  :Author: Ralph Bean <rbean@redhat.com>

"""

import warnings


def send_message(*args, **kwargs):
    try:
        import fedmsg
        fedmsg.send_message(*args, **kwargs)
    except Exception, e:
        warnings.warn(str(e))
