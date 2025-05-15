#!/usr/bin/env python3

# pihole-dashboard
# Copyright (C) 2021-2023  santoru
# Copyright (C) 2023  ameneko
# Copyright (C) 2025  bestbug
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
PIHOLE_PASSWORD = ""
IS_ROTATED = 0
SCREEN_TYPE = "213v2"

OUTPUT_STRING = ""
DISPHASH_FILENAME = "/tmp/.pihole-dashboard-output"
CONFIG_FILENAME = "/etc/pihole-dashboard/config.toml"
SESSION_CACHE_FILE = "/tmp/.pihole-dashboard-session"

# Read config file
try:
    CONFIG = toml.load(CONFIG_FILENAME, _dict=dict)
    INTERFACE = CONFIG["interface"]
    PIHOLE_IP = CONFIG["pihole_ip"]
    PIHOLE_PORT = CONFIG["pihole_port"]
    PIHOLE_PASSWORD = CONFIG["pihole_password"]
    IS_ROTATED = CONFIG["is_rotated"]
    SCREEN_TYPE = CONFIG["screen_type"]
except Exception as e:
    output_error = f"Config can't be parsed! Please check config file. Error: {str(e)}"
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


# Global variable to store CSRF token if needed
csrf_token = None

def save_session(sid, csrf):
    """Save session ID and CSRF token to cache file for reuse"""
    try:
        with open(SESSION_CACHE_FILE, 'w') as f:
            cache_data = {
                'sid': sid,
                'csrf': csrf,
                'timestamp': strftime("%Y-%m-%d %H:%M:%S", localtime())
            }
            f.write(json.dumps(cache_data))
    except Exception:
        # If we can't save the session, just continue without caching
        pass

def load_session():
    """Load session ID and CSRF token from cache file if available"""
    try:
        if os.path.exists(SESSION_CACHE_FILE):
            with open(SESSION_CACHE_FILE, 'r') as f:
                cache_data = json.loads(f.read())
                
                # Set csrf_token global
                global csrf_token
                csrf_token = cache_data.get('csrf')
                
                return cache_data.get('sid')
    except Exception:
        # If we can't load the session, return None to request a new one
        pass
    return None

def validate_session(sid):
    """Test if the cached session is still valid"""
    if not sid:
        return False
        
    headers = {
        'sid': sid,
        'Cookie': f'sid={sid}'
    }
    
    # Add CSRF token if available
    if csrf_token:
        headers['X-CSRF-Token'] = csrf_token
    
    # Try to access the summary API as a test
    try:
        test_url = f"http://{PIHOLE_IP}:{PIHOLE_PORT}/api/stats/summary"
        request = urllib.request.Request(test_url, headers=headers)
        response = urllib.request.urlopen(request)
        # If we get here, the session is valid
        return True
    except Exception:
        # Session invalid, we'll need a new one
        return False

def get_session_id():
    """Get a session ID from the V6 API by authenticating, with caching"""
    # First try to load and validate a cached session
    cached_sid = load_session()
    if cached_sid and validate_session(cached_sid):
        return cached_sid
    
    # If no valid cached session, request a new one
    if not PIHOLE_PASSWORD:
        # Try to access without authentication (if local API auth is disabled)
        return None
        
    auth_url = f"http://{PIHOLE_IP}:{PIHOLE_PORT}/api/auth"
    auth_data = json.dumps({"password": PIHOLE_PASSWORD}).encode('utf-8')
    
    try:
        request = urllib.request.Request(
            auth_url, 
            data=auth_data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(request)
        result = json.load(response)
        
        # Check for the nested session structure (Pi-hole v6)
        if 'session' in result and 'sid' in result['session']:
            # Store CSRF token if available for future requests
            global csrf_token
            if 'csrf' in result['session']:
                csrf_token = result['session']['csrf']
            
            # Save the session for future use
            sid = result['session']['sid']
            save_session(sid, csrf_token)
            return sid
        # Fallback for older API format
        elif 'sid' in result:
            sid = result['sid']
            save_session(sid, None)
            return sid
        
        # If we get here, no valid session ID was found
        sys.exit(f"Failed to find session ID in authentication response: {result}")
    except Exception as e:
        sys.exit(f"Failed to authenticate: {str(e)}")

def update():
    session_id = get_session_id()
    
    # With V6 API, we need to make separate requests
    headers = {}
    if session_id:
        # Pi-hole v6 accepts the session ID in various ways
        # Try setting it as both a header and in a cookie
        headers['sid'] = session_id
        headers['Cookie'] = f'sid={session_id}'
        
        # Add CSRF token if available
        if csrf_token:
            headers['X-CSRF-Token'] = csrf_token
    
    # Get summary stats
    summary_url = f"http://{PIHOLE_IP}:{PIHOLE_PORT}/api/stats/summary"
    
    try:
        request = urllib.request.Request(summary_url, headers=headers)
        response = urllib.request.urlopen(request)
        stats = json.load(response)
    except Exception as e:
        output_string = "Error from API.\nRun pihole-dashboard-draw\nfor details."
        draw_dashboard(output_string)
        output_error = f"API Response Error: {str(e)}"
        sys.exit(output_error)
        
    # Get status
    status_url = f"http://{PIHOLE_IP}:{PIHOLE_PORT}/api/dns/blocking"
    
    try:
        request = urllib.request.Request(status_url, headers=headers)
        response = urllib.request.urlopen(request)
        status = json.load(response)
    except Exception as e:
        output_string = "Error fetching status.\nRun pihole-dashboard-draw\nfor details."
        draw_dashboard(output_string)
        output_error = f"Status API Response Error: {str(e)}"
        sys.exit(output_error)
    
    try:
        ip = ni.ifaddresses(INTERFACE)[ni.AF_INET][0]['addr']
        ip_str = f"[✓] IP of {hostname}: {ip}"
    except KeyError:
        ip_str = "[×] Can't get IP address"
        ip = ""

    if "unique_clients" not in stats:
        # Try to find the data in the v6 API format
        if "clients" in stats and "active" in stats["clients"]:
            unique_clients = stats["clients"]["active"]
        else:
            output_string = "Error parsing API.\nRun pihole-dashboard-draw\nfor details."
            draw_dashboard(output_string)
            output_error = f"API Response missing client data: {stats}"
            sys.exit(output_error)
    else:
        unique_clients = stats.get('unique_clients', 0)

    # Try to get the blocked ads count from either v5 or v6 API format
    if "ads_blocked_today" in stats:
        ads_blocked_today = stats.get('ads_blocked_today', 0)
    elif "queries" in stats and "blocked" in stats["queries"]:
        ads_blocked_today = stats["queries"]["blocked"]
    else:
        output_string = "Error parsing API.\nRun pihole-dashboard-draw\nfor details."
        draw_dashboard(output_string)
        output_error = f"API Response missing blocked ads data: {stats}"
        sys.exit(output_error)

    # Construct status string
    status_str = "[✓] Pi-hole is enabled" if status.get('blocking', False) else "[×] Pi-hole is disabled"
    
    OUTPUT_STRING = ip_str + "\n" + status_str
    OUTPUT_STRING = OUTPUT_STRING + "\n" + f"[✓] There are {unique_clients} clients connected"
    OUTPUT_STRING = OUTPUT_STRING + "\n" + f"[✓] Blocked {ads_blocked_today} ads"

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
