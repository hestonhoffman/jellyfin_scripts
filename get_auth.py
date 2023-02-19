'''
This is needed to grab the access token from the user. 
A regular API token doesn't work for deleting content.
'''

import json, os
from dotenv import load_dotenv
from pprint import pprint
import requests

load_dotenv()
jellyfin_api_token = os.getenv('JELLY_ACCESS_TOKEN')
jelly_url = os.getenv('JELLYFIN_URL')
jelly_user_id = os.getenv('USER_ID')
jelly_user = os.getenv('JELLY_USER')
jelly_pass = os.getenv('JELLY_PASS')

session = requests.Session()
session.headers.update({'accept': 'application/json'})
session.headers.update({'Content-Type': 'application/json'})
session.params.update({'api_key': jellyfin_api_token})
session.params.update({'UserId': jelly_user_id})

def get_token_url():
    return jelly_url + '/Users/AuthenticateByName'

auth_data = {
    'Username': jelly_user,
    'Pw': jelly_pass
}

DATA = json.dumps(auth_data)
DATA = DATA.encode("utf-8")
DATA = bytes(DATA)

auth_url = get_token_url()
auth_token = session.post(auth_url, data=DATA).json()
pprint(auth_token)