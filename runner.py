#!/usr/local/bin/python3

# Tradfri API imports
from pytradfri import Gateway
from pytradfri.api.aiocoap_api import APIFactory
from pytradfri.error import PytradfriError
from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, XYZColor

import asyncio
import argparse

def get_lights():
	""" Gets all of the user's current lights connected to the gateway """
	print("Getting lights..")

def strobe(lights):
	""" Strobe light routine """
	print("Strobe")

def cycle(lights, delay=30):
	""" Cycles through all RGB values, with delay defaulted to 30 seconds for a full change """
	print("Cycle")

async def 

if __name__ == "__main__":
	# Get IP and Security Code of gateway
	p = argparse.ArgumentParser()
	parser.add_argument('host', metavar='IP', type=str,
				help='IP Address of your Tradfri gateway')
	parser.add_argument('code', metavar='C', type=str,
				help='Security key of Tradfri gateway')
	args = parser.parse_args()
	
	# Create APIFactory with credentials
	try:
		# TODO - Figure out how this construction works
		api_f = APIFactory(host=args.host, psk_id=idt, psk=args.code)
	except:
		# TODO - Probably a TradfriError?
		print("Error generating API object for gateway.")
		print("IP: %s" % args.host)
		print("Code: %s" % args.code)
		exit()
	
	# Create request and gateway
	api_r = api_f.request
	gateway = Gateway()
	# TODO - What do these 3 lines do?
	devices = gateway.get_devices()
	devices_c = await api(devices)
	devices = await api(devices_c)

	# TODO - OK to send to routines now
	# TODO - Make routines Async
