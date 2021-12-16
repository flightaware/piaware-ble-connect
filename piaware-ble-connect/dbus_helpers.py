""" This file contains helper functions to interact with systemd services using Python's D-Bus library

"""
import dbus
import logging
import subprocess

from constants import DBUS_SYSTEMD_IFACE, DBUS_SYSTEMD_OBJECT_PATH, DBUS_SYSTEMD_MANAGER_IFACE, DBUS_PROP_IFACE, DBUS_SYSTEMD_UNIT_IFCE

logger = logging.getLogger('piaware_ble_connect')

def stop_systemd_service(service_name):
    logger.debug(f'Stopping {service_name}')

    cmd = ["sudo", "systemctl", "stop", service_name]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def start_systemd_service(service_name):
    logger.debug(f'Starting {service_name}')

    cmd = ["sudo", "systemctl", "start", service_name]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def shutdown_ble_services():
    logger.info(f'Stopping PiAware Bluetooth LE services for piaware configuration')

    stop_systemd_service('piaware-wifi-scan.service')
    stop_systemd_service('piaware-configurator.service')
    stop_systemd_service('piaware-ble-connect.service')

def start_piaware_configurator():
    logger.debug(f'Starting piaware-configurator...')
    start_systemd_service('piaware-configurator.service')


def start_piaware_wifi_scan():
    logger.debug(f'Starting piaware-wifi-scan...')
    start_systemd_service('piaware-wifi-scan.service')