import google
from datetime import datetime, date, timedelta
from typing import Union

import pytz
import requests, re
from attr import dataclass
from environs import Env
import logging
from google.cloud import firestore

logging.basicConfig(level=logging.DEBUG)


def get_netatmo_token() -> dict:
    env = Env()
    env.read_env()

    payload = {'grant_type': 'password',
               'username': env('NETATMO_USERNAME'),
               'password': env('NETATMO_PASS'),
               'client_id': env('NETATMO_CLIENT_ID'),
               'client_secret': env('NETATMO_CLIENT_SECRET'),
               'device_id': env('NETATMO_DEVICE_ID'),
               'scope': 'access_camera access_presence read_camera read_presence read_station',
               }
    try:
        logging.debug("Attempting to retrieve token for client_id %s", payload['client_id'])
        response = requests.post("https://api.netatmo.com/oauth2/token", data=payload)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]
        scope = response.json()["scope"]
        logging.debug("Your access token is %s", access_token)
        logging.debug("Your refresh token is %s", refresh_token)
        return {'access_token': access_token, 'device_id': payload['device_id'], 'created_at': datetime.now()}
    except requests.exceptions.HTTPError as error:
        print(error.response.status_code, error.response.text)


def get_sound_level_cached(netatmo_access_data: dict) -> float:
    """ Returns the sound level (and caches it for one minute not to
    receive a 403) """
    db = firestore.Client()
    doc_ref = db.collection(u'schaltuhr').document(u'soundlevel')
    soundlevel_doc = None

    try:
        doc = doc_ref.get()
        if doc.exists and (doc.to_dict()['created_at'] - datetime.utcnow().replace(tzinfo=pytz.utc)).total_seconds() < 60:
            return doc.to_dict()['soundlevel']
    except google.cloud.exceptions.NotFound:
        pass

    if soundlevel_doc is None:
        soundlevel_doc = {
            'soundlevel': get_sound_level(netatmo_access_data),
            'created_at': datetime.utcnow().replace(tzinfo=pytz.utc)
        }
        doc_ref.set(soundlevel_doc)
    return soundlevel_doc['soundlevel']


def get_sound_level(netatmo_access_data: dict) -> float:
    params = {
        'access_token': netatmo_access_data['access_token'],
        'device_id': netatmo_access_data['device_id']
    }
    try:
        logging.info("Retrieve sound level")
        response = requests.post("https://api.netatmo.com/api/getstationsdata", params=params)
        response.raise_for_status()
        data = response.json()["body"]
        return data['devices'][0]['dashboard_data']['Noise']
    except requests.exceptions.HTTPError as error:
        print(error.response.status_code, error.response.text)


def get_weather_page_content() -> str:
    """ Return source code of the page of the weather state """
    r = requests.get('https://www.tecson-data.ch/zurich/mythenquai/index.php')
    return str(r.content)


def is_it_dark() -> bool:
    """ Returns True if it is dark """
    logging.debug("Retrieve brightness")
    r = get_weather_page_content()
    if r:
        result = re.search(r'>([0-9,]*)&nbsp;W/m', r)
        if result:
            brightness = float(result.group(1).replace(',', '.'))
            logging.debug("Brightness is %f", brightness)
            return brightness < 3
    raise Exception("Could not retrieve brightness")


def contains_valid_template(date: datetime) -> bool:
    """ Retrieves a display program from the past days.
    Find a day when someone was at home.

    At the end of a day, check if there is a day summary.
    A day summary say whether that day can be used as a template.

    Index: Date
    Keys: can_be_used_as_template: Boolean

    """
    db = firestore.Client()
    mindatetime = date.replace(hour=20, minute=0, second=0)
    maxdatetime = date.replace(hour=23, minute=0, second=0)
    docs = db.collection(u'schaltuhr_log_minutely').where('timestamp', '>', mindatetime).where('timestamp', '<',
                                                                                               maxdatetime).stream()
    total_entries = 0
    entries_with_presence = 0

    for doc in docs:
        print(doc.to_dict())
    pass


def update_db_structure():
    """ Compress database  """
    db = firestore.Client()
    docs = db.collection(u'schaltuhr_log').stream()
    items = {'initial': 0, 'converted': 0}
    last_ts = None
    batch = db.batch()
    i = 0
    for doc in docs:
        quantized_time = doc.to_dict()['timestmap'].replace(second=0, microsecond=0)
        items['initial'] += 1
        if quantized_time != last_ts:
            print("Storing " + str(quantized_time))
            last_ts = quantized_time
            items['converted'] += 1

            record = {
                'timestamp': doc.to_dict()['timestmap'],
                'lightlevel': doc.to_dict()['level'],
                'its_day': doc.to_dict()['its_day'],
            }
            key = quantized_time.strftime('%Y-%m-%dT%H:%M')
            new_doc = db.collection('schaltuhr_log_minutely').document(key)
            batch.set(new_doc, record)
            i += 1
            if i == 100:
                batch.commit()
                batch = db.batch()
                i = 0
