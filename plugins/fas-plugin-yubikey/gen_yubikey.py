#!/usr/bin/python

import time, string, sys
from random import choice

try:
    key_num = int(sys.argv[1])
except IndexError:
    print "Please give a key id (usually the users uid)"
    sys.exit(2)

def hex2modhex (string):
    ''' Convert a hex string to a modified hex string '''
    replacement = { '0': 'c',
                    '1': 'b', 
                    '2': 'd',
                    '3': 'e',
                    '4': 'f',
                    '5': 'g',
                    '6': 'h',
                    '7': 'i',
                    '8': 'j',
                    '9': 'k',
                    'a': 'l',
                    'b': 'n',
                    'c': 'r',
                    'd': 't',
                    'e': 'u',
                    'f': 'v' }
    new_string = ''
    for letter in string:
        new_string = new_string + replacement[letter]
    return new_string

def gethexrand(length):
    return ''.join([choice('0123456789abcdef') for i in range(length)]).lower()

now = time.strftime("%Y-%m-%dT%H:%M:%S")
print "# ykksm 1"
print "# serialnr,identity,internaluid,aeskey,lockpw,created,accessed[,progflags]"
hexctr = "%012x" % key_num
modhexctr = hex2modhex(hexctr)
internaluid = gethexrand(12)
aeskey = gethexrand(32)
lockpw = gethexrand(12)
print "%s,%s,%s,%s,%s,%s," % (key_num, modhexctr, internaluid, aeskey, lockpw, now)
