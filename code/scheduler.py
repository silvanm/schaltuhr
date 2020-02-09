import logging
# see https://stackoverflow.com/a/20280587/2454815
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

import random
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Tuple
import requests

from config import switches, days_events
from main import env
from schaltuhr import get_sun
import sched, time


def get_random_time_in_range(range: Tuple[str, str]) -> int:
    """
    :param range:
    :return:
    """
    now = datetime.now()
    start_struct = time.strptime(range[0], '%H:%M')
    end_struct = time.strptime(range[1], '%H:%M')
    range_start_time = now.replace(hour=start_struct.tm_hour, minute=start_struct.tm_min)
    range_end_time = now.replace(hour=end_struct.tm_hour, minute=end_struct.tm_min)
    range = range_end_time - range_start_time
    randomized_time = range_start_time.timestamp() + random.randint(0, range.seconds)
    return int(randomized_time)


def send_command_to_switch(switch: str, command: str):
    assert switch in switches
    assert command in ['on', 'off']

    requests.post(
        f'https://maker.ifttt.com/trigger/light-{switch}-{command}/with/key/' + env('IFTTT_KEY'))


def get_random_time_around(time: datetime, interval_minutes: int = 30):
    return random.randint(time.timestamp() - interval_minutes * 60, time.timestamp() + interval_minutes * 60)


def generate_program():
    """ generate a program for the current day """
    sun = get_sun()
    sunrise = sun.get_sunrise_time() + timedelta(minutes=30)
    sunset = sun.get_sunset_time() - timedelta(minutes=30)

    program = {}

    # Iterate over each switch
    for id, config in switches.items():
        program[id] = OrderedDict()
        # morning
        if config['morning']:
            program[id][get_random_time_in_range(days_events['getting_up'])] = 'on'
            program[id][get_random_time_around(sunrise, interval_minutes=15)] = 'off'

        # evening
        if config['evening']:
            program[id][get_random_time_around(sunset, interval_minutes=15)] = 'on'
            program[id][get_random_time_in_range(days_events['bedtime'])] = 'off'

    return program


def print_program(program: dict):
    logging.info('Program:')
    for switch_id in switches.keys():
        for tm, event in program[switch_id].items():
            logging.info(f'Switch {switch_id}: {datetime.fromtimestamp(tm)}: {event}')


def populate_scheduler(program: dict) -> sched.scheduler:
    """ Generate a program for today and add it to the scheduler """
    scheduler = sched.scheduler(time.time, time.sleep)

    now = datetime.now().timestamp()
    for switch_id in switches.keys():
        current_state = 'off'
        for tm, command in program[switch_id].items():
            if tm < now:
                current_state = command
            else:
                logging.info(f'Scheduling: Switch {switch_id}: {datetime.fromtimestamp(tm)}: {command}')
                scheduler.enterabs(tm, 1, lambda: send_command_to_switch(switch_id, command))
        logging.info(f'Setting current state for Switch {switch_id}: {current_state}')
        send_command_to_switch(switch_id, current_state)
    return scheduler


while True:
    logging.info(f"Prepare program for {datetime.strftime(datetime.now(), '%d.%m.%Y')} ")
    program = generate_program()
    print_program(program)
    scheduler = populate_scheduler(program)
    scheduler.run()
    wait_until = datetime.now().replace(hour=0).timestamp() + 24 * 3600
    wait_seconds = int(wait_until - datetime.now().timestamp())
    logging.info(f"Waiting until the next midnight for a new program ({wait_seconds} seconds)")
    time.sleep(wait_seconds)
