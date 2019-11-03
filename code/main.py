from datetime import datetime

from flask import Flask, request, jsonify, g, send_from_directory
import requests
import logging
from google.cloud import datastore, firestore
from schaltuhr import is_it_dark, get_sound_level
import schaltuhr
from environs import Env

app = Flask(__name__, static_folder='static')
logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

last_level = None

env = Env()
env.read_env()


def get_netatmo_token():
    if 'netatmo_token' in g:
        age = g.netatmo_token.created_at - datetime.now().day
        if age < 1:
            logging.debug(f'Log light level. Threshold: {threshold}')
            return g.netatmo_token
    else:
        g.netatmo_token = None

    try:
        logging.info('Getting Netatmo token')
        g.netatmo_token = schaltuhr.get_netatmo_token()
    except Exception as e:
        logging.warning('Failed retrieving the Netatmo token', exc_info=True)
    return g.netatmo_token


@app.route("/")
def home():
    return app.send_static_file('index.html')


@app.route('/light', methods=['GET'])
def lightlevel():
    """ Post the current light level """
    global last_level

    # Load the threshold
    client = datastore.Client()
    key = client.key('schaltuhr', 'threshold')
    try:
        threshold = client.get(key)['level']
        logging.debug(f'Log light level. Threshold: {threshold}')
    except TypeError:
        logging.warning(f'Could not load threshold from datastore. Setting it to default value.')
        threshold = 600

    # Get the reading and store it in the datastore
    lightlevel = int(request.args.get('level'))
    quantized_time = datetime.now().replace(second=0, microsecond=0)
    key = client.key('schaltuhr_log_minutely', quantized_time.strftime('%Y-%m-%dT%H:%M'))
    its_day = not is_it_dark()
    logging.debug(f'Light level={lightlevel}; its_day={its_day}')
    entity = datastore.Entity(key=key)
    entity.update({
        'lightlevel': lightlevel,
        'soundlevel': get_sound_level(get_netatmo_token()),
        'timestamp': datetime.now(),
        'its_day': its_day,
    })
    client.put(entity)

    # Act on the light
    if int(lightlevel) > threshold:
        if last_level == 'on' or last_level is None:
            logging.info(f'Lightlevel: {lightlevel}. Turn light on')
            requests.post(
                'https://maker.ifttt.com/trigger/light-on/with/key/' + env('IFTTT_KEY'))
            last_level = 'off'
    else:
        if last_level == 'off' or last_level is None:
            logging.info(f'Lightlevel: {lightlevel}. Turn light off')
            requests.post(
                'https://maker.ifttt.com/trigger/light-off/with/key/' + env('IFTTT_KEY'))
            last_level = 'on'

    return "OK"


@app.route('/threshold', methods=['GET', 'POST'])
def threshold():
    """ Store or retrieve the light threshold """
    client = datastore.Client()
    key = client.key('schaltuhr', 'threshold')
    if request.method == 'POST':
        level = int(request.form['level'])
        assert level < 1024
        entity = datastore.Entity(key=key)
        entity.update({'level': level})
        client.put(entity)
        # Then get by key for this entity
        return f'Threshold {level} stored.'
    else:
        result = client.get(key)
        return result


@app.route('/history', methods=['GET'])
def history():
    """ Return the measurements """
    db = firestore.Client()
    docs = db.collection('schaltuhr_log_minutely').stream()
    measurements = []
    for doc in docs:
        d = doc.to_dict()
        measurements.append((d['timestamp'], d['lightlevel'], d['its_day'],
                             d['soundlevel'] if 'soundlevel' in d else 0))
    return jsonify(measurements)


if __name__ == "__main__":
    # in PyCharm this is igored.
    app.run(debug=True, host='0.0.0.0', port=5000)
