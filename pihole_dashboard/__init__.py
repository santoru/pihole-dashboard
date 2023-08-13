#!/usr/bin/env python3

# pihole-dashboard
# Copyright (C) 2021-2023  santoru
# Copyright (C) 2023  ameneko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import socket
from time import localtime, strftime
import urllib.request
import json
import os
import sys
import toml
import hashlib
import netifaces as ni
from PIL import Image, ImageFont, ImageDraw

if os.geteuid() != 0:
    sys.exit("You need root permissions to access E-Ink display, try running with sudo!")

INTERFACE = "wlan0"
PIHOLE_IP = "127.0.0.1"
PIHOLE_PORT = 80
PIHOLE_APITOKEN = ""
IS_ROTATED = 0
SCREEN_TYPE = "213v2"

OUTPUT_STRING = ""
DISPHASH_FILENAME = "/tmp/.pihole-dashboard-output"
CONFIG_FILENAME = "/etc/pihole-dashboard/config.toml"

# Read config file
try:
    CONFIG = toml.load(CONFIG_FILENAME, _dict=dict)
    INTERFACE = CONFIG["interface"]
    PIHOLE_IP = CONFIG["pihole_ip"]
    PIHOLE_PORT = CONFIG["pihole_port"]
    PIHOLE_APITOKEN = CONFIG["pihole_api_token"]
    IS_ROTATED = CONFIG["is_rotated"]
    SCREEN_TYPE = CONFIG["screen_type"]
except TomlDecodeError:
    output_error = "Config can't be parsed! Please check config file."
    sys.exit(output_error)

hostname = socket.gethostname()
font_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')
font_name = os.path.join(font_dir, "font.ttf")
font16 = ImageFont.truetype(font_name, 16)
font12 = ImageFont.truetype(font_name, 12)

# Determine display type and clear
if SCREEN_TYPE == "213v2":
  from waveshare_epd import epd2in13_V2
  epd = epd2in13_V2.EPD()
  epd.init(epd.FULL_UPDATE)
elif SCREEN_TYPE == "213v3":
  from waveshare_epd import epd2in13_V3
  epd = epd2in13_V3.EPD()
  epd.init()
  epd.Clear(0xFF)


def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False


def draw_dashboard(out_string=None):
    # Draw a white canvas
    image = Image.new("1", (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)

    # Get Time
    t = strftime("%H:%M:%S", localtime())
    time_string = "Updated: {}".format(t)

    # Get Version
    cmd = "/usr/local/bin/pihole -v"
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output = process.stdout.read().decode().split('\n')
    version = output[0].split("(")[0].strip()

    # Draw frame & text
    draw.rectangle([(0, 105), (250, 122)], fill=0)
    if out_string is not None:
        draw.text((0, 0), out_string, font=font16, fill=0)
    draw.text((5, 106), version, font=font12, fill=1)
    draw.text((150, 106), time_string, font=font12, fill=1)
    if (IS_ROTATED == 1):
        image = image.rotate(180)
    epd.display(epd.getbuffer(image))


def update():
    url = "http://{}:{}/admin/api.php?summary&auth={}".format(PIHOLE_IP, PIHOLE_PORT, PIHOLE_APITOKEN)
    r = json.load(urllib.request.urlopen(url))

    try:
        ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
    except KeyError:
        ip_str = "[×] Can't get IP address"
        ip = ""

    if "unique_clients" not in r:
        output_string = "Error from API.\nRun pihole-dashboard-draw\nfor details."
        draw_dashboard(output_string)
        output_error = "API Response: {}".format(r)
        sys.exit(output_error)

    unique_clients = r['unique_clients']
    ads_blocked_today = r['ads_blocked_today']

    if valid_ip(ip):
        ip_str = "[✓] IP of {}: {}".format(hostname, ip)

    cmd = "/usr/local/bin/pihole status"
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output = process.stdout.read().decode().split('\n')

    OUTPUT_STRING = ip_str + "\n" + output[0].strip().replace('✗', '×') + "\n" + output[6].strip().replace('✗', '×')
    OUTPUT_STRING = OUTPUT_STRING + "\n" + "[✓] There are {} clients connected".format(unique_clients)
    OUTPUT_STRING = OUTPUT_STRING + "\n" + "[✓] Blocked {} ads".format(ads_blocked_today)

    hash_string = hashlib.sha1(OUTPUT_STRING.encode('utf-8')).hexdigest()
    try:
        hash_file = open(DISPHASH_FILENAME, "r+")

    except FileNotFoundError:
        os.mknod(DISPHASH_FILENAME)
        hash_file = open(DISPHASH_FILENAME, "r+")

    file_string = hash_file.read()
    if file_string != hash_string:
        hash_file.seek(0)
        hash_file.truncate()
        hash_file.write(hash_string)
    draw_dashboard(OUTPUT_STRING)
