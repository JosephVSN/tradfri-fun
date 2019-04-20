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
import json
import requests

# Constants
CONFIG_FILE = 'tradfri_standalone_psk.conf'
STEP = 1000   # Used for sleeps and transition_time
SPOTIFY_URL = "https://api.spotify.com/v1/me/player/currently-playing"

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
parser.add_argument('-c', '--cycle', action="store_true", required=False,
                    help='Smooth cycle through preset colours')
parser.add_argument('-s', '--strobe', action="store_true", required=False,
                    help='Emulate strobe lights')
parser.add_argument('-b', '--brightness', action="store_true", required=False,
                    help="Slide brightness from 0 to 100 back to 0.")
parser.add_argument('-K', '--key', dest='key', required=False,
                    help='Key found on your Tradfri gateway')
args = parser.parse_args()

# If no cycle was picked then default to cycle
if not args.cycle and not args.strobe and not args.brightness:
    args.cycle = True
# Force strobe and cycle to be mutually exclusive
if args.cycle and args.strobe:
    raise RuntimeError("Cycle and Strobe are mutually exclusive; pick one command.")
# Look for host in JSON; write if new
if args.host not in load_json(CONFIG_FILE) and args.key is None:
    print("Please provide the 'Security Code' on the back of your "
          "Tradfri gateway:", end=" ")
    key = input().strip()
    if len(key) != 16:
        raise PytradfriError("Invalid 'Security Code' provided.")
    else:
        args.key = key

def get_bpm(title, artist, bpm_key):
    # Get BPM
    url_start = "https://api.getsongbpm.com/search/?api_key="
    url_end = "&type=both&lookup="
    title_fmt = title.replace(" ", "+")
    artist_fmt = artist.replace(" ", "+")
    url = url_start + bpm_key + url_end + "song: " + title_fmt + " artist:" + artist_fmt
    r = requests.get(url)
    if r.status_code != 200:
        sys.exit()
    bpm_json = r.json()['search']
    try:
        bpm = bpm_json[0]['tempo']
    except:
        print("no result")
        sys.exit()
    print("\tBPM is %s" % bpm)
    return int(bpm)

async def slider_brightness(light, api, delay=5):
    """ Slides through all brightnesses 0 - 100 and back down. """
    print("Starting brightness slider...")
    while(True):
        for i in range(0, 101):
            await api(light.light_control.set_dimmer(i, transition_time=delay*9))
            await asyncio.sleep(delay)
        for i in range(99, -1):
            await api(light.light_control.set_dimmer(i, transition_time=delay*9))
            await asyncio.sleep(delay)

async def cycle(light, api, delay=5):
    """ Cycles through all RGB values, with delay defaulted to 30 seconds for a full change """
    print("Starting cycle..")
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

async def strobe(light, api):
    """ Does a 'strobe'-esque effect with the preset colours """
    while(True):
        shuffle(CYCLE_COLORS)
        title = ""
        for c in CYCLE_COLORS:
            xyz = convert_color(sRGBColor(c[0], c[1], c[2]), XYZColor,
                                observer='2', target_illuminant='d65')
            xy = int(xyz.xyz_x), int(xyz.xyz_y)
            await api(light.light_control.set_xy_color(xy[0], xy[1], transition_time=.5))
            await asyncio.sleep(.1)

async def strobe_bpm(light, api, spotify_key, bpm_key):
    """ Does a 'strobe'-esque effect with the preset colours """
    print("Starting strobe..")
    while(True):
        shuffle(CYCLE_COLORS)  # Randomize order
        title = ""
        for c in CYCLE_COLORS:
            r = requests.get(SPOTIFY_URL, headers={"Authorization" : "Bearer " + spotify_key})
            if r.status_code != 200:
                print("Bad status code")
                return
            r = r.json()
            if r == "" or r['item']['name'] != title:
                title = r['item']['name']
                artist = r['item']['artists'][0]['name']
                print("Artist: %s\nTitle: %s" % (artist, title))
                bps = float(get_bpm(title, artist, bpm_key) / 60)
            # Convert to CIE XYZ colour
            xyz = convert_color(sRGBColor(c[0], c[1], c[2]), XYZColor,
                                observer='2', target_illuminant='d65')
            xy = int(xyz.xyz_x), int(xyz.xyz_y)
            # Send command to light then sleep for smooth transition
            await api(light.light_control.set_xy_color(xy[0], xy[1], transition_time=bps/4))

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
     
    # Get auth
    with open("tokens.json") as f:
        js = json.load(f)
        spotify_key = js['spotify']['auth']
        bpm_key = js['bpm']['api_key']   
 
    # Check what procedure to run
    if args.cycle:
        await cycle(light, api)
    elif args.strobe:
        await strobe(light, api)
    elif args.brightness:
        await slider_brightness(light, api)
    print("Run ended.")
    return  # shutdown() throws an error so just exit
    # TODO - Find a way to actually shutdown

# Start async loop on run
try:
	asyncio.get_event_loop().run_until_complete(run())
except RuntimeError:
	print("Done cycling.")
