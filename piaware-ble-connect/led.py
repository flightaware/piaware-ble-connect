#!/usr/bin/env python3

# Helper functions to control LEDs on the Pi

import os

def blink(led_num):
    cmd = f"echo timer | sudo tee /sys/class/leds/{led_num}/trigger 1>/dev/null"
    os.system(cmd)

def restore_default(led_num):

    default_triggers = {
        '9000c1': 'actpwr', # Pi Zero W
        '902120': 'actpwr', # Pi Zero 2 W
        '9020e0': 'mmc0',   # Pi 3A+
        'a02100': 'mmc0',   # Pi Compute Module 3
        'a02082': 'mmc0',   # Pi 3B
        'a22082': 'mmc0',   # Pi 3B
        'a32082': 'mmc0',   # Pi 3B
        'a020d3': 'mmc0',   # Pi 3B+
        'a02100': 'mmc0',   # Pi Compute Module 3+
        'a03111': 'mmc0',   # Pi 4 1gb
        'b03111': 'mmc0',   # Pi 4 2gb
        'c03111': 'mmc0'    # Pi 4 3gb
    }

    # Get cpu revision
    with open('/proc/cpuinfo', 'r') as f:
        cpuinfo = f.readlines()
        for line in cpuinfo:
            fields = line.split(':')
            if fields[0].strip() == 'Revision':
                revision = fields[1].strip()
                break

    # Set trigger based on Pi's default
    if revision in default_triggers:
        trigger = default_triggers[revision]
    else:
        trigger = 'mmc0'

    cmd = f"echo {trigger} | sudo tee /sys/class/leds/{led_num}/trigger 1>/dev/null"
    os.system(cmd)


if __name__ == '__main__':
   restore_default('led0')
