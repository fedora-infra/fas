#!/usr/bin/env python

import os
import requests
import json

from cryptography.fernet import Fernet
from getpass import getpass


FAS_URL = str('http://0.0.0.0:6543/api')
HEADERS = {'content-type': 'application/json'}

get_people = '/people'
get_person = '/people/username/laxathom'


API_TOKEN = {'apikey': u'8324fbbf666c4bfecc0b2ea7dbca43cb35c05c34'}
SECRET = str('zD5Afn6JN9je6WIc4AD1L_NIS3o6bQnFrFH-q_PiweU=')


if __name__ == '__main__':

    username = raw_input('Enter your username: ')
    password = getpass(prompt='Enter your password: ')

    # Set up user's credentials to request login
    credentials = '{"login": "%s", "password": "%s"}' % (username, password)
    cipher = Fernet(SECRET)
    private_data = cipher.encrypt(credentials)

    payload = {
        "credentials": str(private_data),
    }

    rq = requests.post(
        FAS_URL + '/request-login',
        data=json.dumps(payload),
        headers=HEADERS,
        params=API_TOKEN
    )

    # print(rq.text)

    if rq.status_code == 200:
        rsl = rq.json()
        rsl = rsl['RequestResult']

        # 0 Stands for LOGIN_SUCCEED
        if rsl['login_status'] == 0:

            # Grab returned auth token
            auth = cipher.decrypt(bytes(rsl['data']))
            auth = json.loads(auth)
            HEADERS['Cookie'] = auth['auth_token']

            # Set up client's ID to regsiter it to FAS server.
            # token will be generated from Ipsilon (OAuth way)
            app = {
                'name': 'GNOME Online Account Client 2.1',
                'token': '23092iu3329120di30932id0932i2109id3d'
            }

            # Serialize and sign above ID before sending it to server
            payload = {}
            payload['credentials'] =  cipher.encrypt(bytes(app))

            nrq = requests.post(
                FAS_URL + '/request-perm/org.fedoraproject.fas.user.info',
                data=json.dumps(payload),
                headers=HEADERS,
                params=API_TOKEN
            )

            print(nrq.text)

            # Now it's up to the auth provider to pass to the client valid token.
    else:
        print('Oh, snap! Something bad happened:\n%s' % rq.text)
