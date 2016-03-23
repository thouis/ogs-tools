import json
import os.path

try:
    from urllib import urlencode
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode

def fetch_token():
    d = json.loads(open('.auth').read())
    values = {'client_id': d['CLIENT_ID'],
              'client_secret': d['CLIENT_SECRET'],
              'grant_type': 'password',
              'username': d['USERNAME'],
              'password': d['PASSWORD']}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = urlencode(values).encode('UTF-8')
    request = Request('https://online-go.com/oauth2/access_token/', data=data, headers=headers)
    response_body = json.loads(urlopen(request).read().decode('UTF-8'))
    return response_body['access_token']

def token(tok=[]):
    return fetch_token()
