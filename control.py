#!/usr/bin/env python3
"""
TODO - Add new header
"""

# Hack to allow relative import above top level package -- from example
import sys
import os
folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa

# Pytradfri & related imports
from pytradfri import Gateway
from pytradfri.api.aiocoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json
from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, XYZColor

# etc. imports
from random import shuffle
import asyncio
import uuid
import argparse

# Constants
CONFIG_FILE = 'tradfri_standalone_psk.conf'
STEP = 1000   # Used for sleeps and transition_time

# Color definitions and a list containing them
BLUE      = (0, 0, 100)
RED       = (0, 0, 200)
GREEN     = (0, 120, 70)
WHITE     = (0, 50, 100)
YELLOW    = (50, 100, 110)
ORANGE    = (150, 40, 10)
PURPLE    = (0, 0, 115)
PINK      = (0, 0, 150)
CYCLE_COLORS = [BLUE, RED, GREEN, WHITE, YELLOW, ORANGE, PURPLE, PINK]

# Setup argparse -- From example
parser = argparse.ArgumentParser()
parser.add_argument('host', metavar='IP', type=str,
                    help='IP Address of your Tradfri gateway')
parser.add_argument('-K', '--key', dest='key', required=False,
                    help='Key found on your Tradfri gateway')
args = parser.parse_args()

# Look for host in JSON; write if new
if args.host not in load_json(CONFIG_FILE) and args.key is None:
    print("Please provide the 'Security Code' on the back of your "
          "Tradfri gateway:", end=" ")
    key = input().strip()
    if len(key) != 16:
        raise PytradfriError("Invalid 'Security Code' provided.")
    else:
        args.key = key

async def cycle(light, api, delay=5):
    """ Cycles through all RGB values, with delay defaulted to 30 seconds for a full change """
    print("Starting cycle..")
    ui = ""
    while(True):
        shuffle(CYCLE_COLORS)  # Randomize order - TODO does this work?
        for c in CYCLE_COLORS:
            # Convert to CIE XYZ colour
            xyz = convert_color(sRGBColor(c[0], c[1], c[2]), XYZColor,
                                observer='2', target_illuminant='d65')
            xy = int(xyz.xyz_x), int(xyz.xyz_y)
            # Send command to light then sleep for smooth transition
            await api(light.light_control.set_xy_color(xy[0], xy[1], transition_time=delay*9))
            await asyncio.sleep(delay)

async def run():
    # Assign configuration variables.
    # The configuration check takes care they are present.
    conf = load_json(CONFIG_FILE)
    try:
        identity = conf[args.host].get('identity')
        psk = conf[args.host].get('key')
        api_factory = APIFactory(host=args.host, psk_id=identity, psk=psk)
    except KeyError:
        identity = uuid.uuid4().hex
        api_factory = APIFactory(host=args.host, psk_id=identity)

        try:
            psk = await api_factory.generate_psk(args.key)
            print('Generated PSK: ', psk)

            conf[args.host] = {'identity': identity,
                               'key': psk}
            save_json(CONFIG_FILE, conf)
        except AttributeError:
            raise PytradfriError("Please provide the 'Security Code' on the "
                                 "back of your Tradfri gateway using the "
                                 "-K flag.")

    # Create API devices -- from example
    api = api_factory.request
    gateway = Gateway()
    devices_command = gateway.get_devices()
    devices_commands = await api(devices_command)
    devices = await api(devices_commands)
    lights = [dev for dev in devices if dev.has_light_control]
    light = None
    # Find a bulb that can set color -- from example
    for dev in lights:
        if dev.light_control.can_set_color:
            light = dev
            break
    if not light:
        print("No color bulbs found")
        return
    
    # Run cycle
    await cycle(light, api)
    print("Run ended.")
    return  # shutdown() throws an error so just exit
    # TODO - Find a way to actually shutdown

# Start async loop on run
try:
	asyncio.get_event_loop().run_until_complete(run())
except RuntimeError:
	print("Done cycling.")