#!/usr/bin/python3

import requests, os, json, pathlib, logging
from dotenv import load_dotenv
from pprint import pprint
from datetime import datetime
from dateutil import parser

class MissingVariableError(Exception):
    def __init__(self, item):
        self.item = item
        message = f'Variable {item} not assigned. Set it as an environment variable.'
        print(message)
        logging.error(message)

class MissingUserError(Exception):
    def __init__(self, name):
        self.name = name
        message = f'USER_ID not set. Tried to assign it with user "{name}". But the user was not found. '\
            'Check your spelling and make sure the user exists or set the USER_ID environment '\
            'variable if you already know the user ID.'
        print(message)
        logging.error(message)

class ApiCallFail(Exception):
    def __init__(self, message):
        self.message = message
        print(message)
        logging.error(message)

# Set up logging
script_location = str(pathlib.Path(__file__).parent.parent.resolve())
log_location = script_location + '/deletion_log.log'
logging.basicConfig(
    filename=log_location,
    encoding='utf-8',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def check_envs(required_envs):
    for item in required_envs:
        content = os.getenv(item)
        if not content:
            raise MissingVariableError(item)

def get_user_id(user):
    url = jelly_url + '/Users'
    users = session.get(url)
    if users.ok:
        for user_data in users.json():
            if user_data['Name'] == user:
                return(user_data['Id'])
            else:
                raise MissingUserError(user)
    else:
        raise ApiCallFail(f'User ID retrieval failed with {users.reason}. Check your access token')

def retrieve_access_token(admin_user, admin_password):
    url = jelly_url + '/Users/AuthenticateByName'

    auth_data = {
        'Username': admin_user,
        'Pw': admin_password
    }

    DATA = json.dumps(auth_data)
    DATA = DATA.encode("utf-8")
    DATA = bytes(DATA)

    auth_token = session.post(url, data=DATA).json()
    return(auth_token['AccessToken'])

def get_access_token():
    if os.getenv('JELLY_ACCESS_TOKEN') is not None:
        return os.getenv('JELLY_ACCESS_TOKEN')
    else:
        admin_user = os.getenv('JELLY_ADMIN_USER')
        admin_password = os.getenv('JELLY_ADMIN_PASSWORD')
        token = retrieve_access_token(admin_user, admin_password)
        return token

def get_items_to_delete():
    search_query = ('&').join([
        'Recursive=true',
        'IsPlayed=true',
        'SortOrder=Ascending',
        'isFavorite=false'
    ])

    url = jelly_url + '/Items?' + search_query
    return session.get(url).json()

def delete_bool(date_played):
    last_played = parser.parse(date_played, ignoretz=True)
    time_delta = time_now - last_played
    if time_delta.days > 6:
        return True
    else:
        return False

time_now = datetime.utcnow()

# Make sure the minimum required environment variables are set
required_envs = [
    'JELLY_USER',
    'JELLY_URL',
    'JELLY_API_TOKEN',
    'JELLY_ADMIN_USER',
    'JELLY_ADMIN_PASSWORD'
]

load_dotenv()
check_envs(required_envs)
jelly_user = os.getenv('JELLY_USER')
jelly_url = os.getenv('JELLY_URL')
jelly_api_token = os.getenv('JELLY_API_TOKEN')

session = requests.Session()
session.headers.update({'Content-Type': 'application/json'})
session.params.update({'api_key': jelly_api_token})

# Replace the api token with an access token
# An access token is required to delete media. An API key,
# admin user, and admin password are required to retrieve it.
# I don't know why this is the case, but it's very annoying.
jelly_api_token = get_access_token()
session.params.update({'api_key': jelly_api_token})

# Assign USER_ID if set, else retrieve it.
if os.getenv('USER_ID') is not None:
    jelly_user_id = os.getenv('USER_ID')
else: 
    jelly_user_id = get_user_id(jelly_user)
session.params.update({'UserId': jelly_user_id})

# Retrieve a list of watched episodes
item_data = get_items_to_delete()
# Retrieve a list of watched movies
# movies_info = get_movies_to_delete()

media_to_delete = []

# Create a simpler delection dictionary
for entry in item_data['Items']:
    entry_dict = {}
    entry_dict['Id'] = entry['Id']
    entry_dict['LastPlayedDate'] = entry['UserData']['LastPlayedDate']
    entry_dict['Played'] = entry['UserData']['Played']
    if entry['Type'] == 'Episode':
        entry_dict['EpName'] = entry['Name']
        entry_dict['EpNumber'] = entry['IndexNumber'] 
        entry_dict['SeasonName'] = entry['SeasonName']
        entry_dict['SeriesName'] = entry['SeriesName']
    else:
        entry_dict['Name'] = entry['Name']
    media_to_delete.append(entry_dict)

deleted_count = 0

for entry in media_to_delete:
    delete = delete_bool(entry['LastPlayedDate'])
    try:
        name_string = f'TV: {entry["SeriesName"]}, Episode {entry["EpNumber"]}'
    except:
        name_string = f'Movie: {entry["Name"]}'
    print(f'Checking entry \x1b[3m{name_string}\x1b[0m')
    if delete:
        deleted_count += 1
        deletion = session.delete(jelly_url + '/Items/' + entry['Id'])
        if deletion.ok:
            logging.info(f'Deleted {entry["SeriesName"]}: Episode {entry["EpNumber"]}')
            print(f'Deleted {name_string}')
        else:
            print(f'\x1b[31mWARN\x1b[0m:Deletion failed with {deletion.text}')
            logging.warning(f'Failed to delete {entry["SeriesName"]}: Episode {entry["EpNumber"]}')
            logging.warning(deletion.text)
    else:
        print(f'\t\x1b[32mTime threshold not met for {name_string}. Passing\x1b[0m')        

if deleted_count > 0:
    logging.info('Deletion completed')
else:
    logging.info('Script completed. Nothing to delete')
