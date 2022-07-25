#!/usr/bin/env python3

# Helper functions to control LEDs on the Pi

import os

def blink(led_num):
    cmd = f"echo timer | sudo tee /sys/class/leds/{led_num}/trigger 1>/dev/null"
    os.system(cmd)


# Read default trigger saved in /run/ directory
def restore_default(led_num):
    try:
        with open('/run/piaware-ble-connect/trigger', 'r') as f:
            trigger = f.read()
    except FileNotFoundError as e:
        # Default to mmc0 if we can't read the file
        trigger = 'mmc0'

    cmd = f"echo {trigger} | sudo tee /sys/class/leds/{led_num}/trigger 1>/dev/null"
    os.system(cmd)
