#!/usr/bin/python3

import requests
from dotenv import load_dotenv
import os
from pprint import pprint
import pathlib
from datetime import datetime
from dateutil import parser
import logging

time_now = datetime.utcnow()

script_location = str(pathlib.Path(__file__).parent.resolve())
# Set up logging
log_location = script_location + '/deletion_log.log'
logging.basicConfig(
    filename=log_location,
    encoding='utf-8',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
session.params.update({'password': jelly_pass})

def version_url():
    return jelly_url + '/System/Info'

def users_url():
    return jelly_url + '/Users'

def items_url():
    search_query = ('&').join([
        'Recursive=true',
        'excludeItemTypes=Movie',
        'IsPlayed=true',
        'SortBy=Type,SeriesName,ParentIndexNumber,IndexNumber,Name',
        'SortOrder=Ascending'
    ])

    return jelly_url + '/Items?' + search_query

def delete_bool(date_played):
    last_played = parser.parse(date_played, ignoretz=True)
    time_delta = time_now - last_played
    if time_delta.days > 6:
        return True
    else:
        return False

'''
TODO: 
- Find user_id from supplied user

if not jelly_user_id:
    url = users_url()
    serverinfo = session.get(url).json()[0]["Name"]
    pprint(serverinfo)
'''

# get_user = session.get(users_url()).json()
# pprint(get_user)

get_url = items_url()
serverreply = session.get(get_url)

serverinfo = session.get(get_url).json()
# pprint(serverinfo)

media_to_delete = []

# create a simpler dict for each time
for entry in serverinfo['Items']:
    entry_dict = {}
    entry_dict['EpNumber'] = entry['IndexNumber']
    entry_dict['Id'] = entry['Id']
    entry_dict['EpName'] = entry['Name'] if entry['Name'] else 'NA'
    entry_dict['SeasonName'] = entry['SeasonName']
    entry_dict['SeriesName'] = entry['SeriesName']
    entry_dict['LastPlayedDate'] = entry['UserData']['LastPlayedDate']
    entry_dict['Played'] = entry['UserData']['Played']
    media_to_delete.append(entry_dict)

deleted_count = 0

for entry in media_to_delete:
    delete = delete_bool(entry['LastPlayedDate'])
    episode_string = f'{entry["SeriesName"]}, Episode {entry["EpNumber"]}'
    print(f'Checking entry {episode_string}')
    if delete:
        deleted_count += 1
        deletion = session.delete(jelly_url + '/Items/' + entry['Id'])
        if deletion.ok:
            logging.info(f'Deleted {entry["SeriesName"]}: Episode {entry["EpNumber"]}')
            print(f'Deleted {episode_string}')
        else:
            print(f'Deletion failed with {deletion.text}')
            logging.warning(f'Failed to delete {entry["SeriesName"]}: Episode {entry["EpNumber"]}')
            logging.warning(deletion.text)
    else:
        print(f'Time threshold not met for {episode_string}. Passing')        

if deleted_count > 0:
    logging.info('Deletion completed')
else:
    logging.info('Script completed. Nothing to delete')
