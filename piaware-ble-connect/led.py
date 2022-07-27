#!/usr/bin/env python3

# Helper functions to control LEDs on the Pi

import logging
import subprocess

logger = logging.getLogger('piaware_ble_connect')

def blink(led_num):
    logger.info(f'Setting sysfs {led_num} trigger: trigger')

    subprocess.run(['sudo', 'tee', f'/sys/class/leds/{led_num}/trigger'], text=True, input="timer\n", stdout=subprocess.DEVNULL, check=True)

# Read default trigger saved in /run/ directory
def restore_default(led_num):
    try:
        with open('/run/piaware-ble-connect/trigger', 'r') as f:
            trigger = f.read()
    except FileNotFoundError as e:
        # Fallback to mmc0 if we can't read the file for some reason
        trigger = 'mmc0'

    logger.info(f'Setting sysfs {led_num} trigger: {trigger}')

    subprocess.run(['sudo', 'tee', f'/sys/class/leds/{led_num}/trigger'], text=True, input=f'{trigger}\n', stdout=subprocess.DEVNULL, check=True)
