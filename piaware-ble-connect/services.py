""" This file contains helper functions to enable/disable BLE services

"""
import logging
import subprocess

logger = logging.getLogger('piaware_ble_connect')

def stop_systemd_service(service_name):
    logger.debug(f'Stopping {service_name}')

    cmd = ["sudo", "systemctl", "stop", service_name]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_systemd_service(service_name):
    logger.debug(f'Starting {service_name}')

    cmd = ["sudo", "systemctl", "start", service_name]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def restart_systemd_service(service_name):
    logger.debug(f'Restarting {service_name}')

    cmd = ["sudo", "systemctl", "restart", service_name]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def shutdown_ble_services():
    logger.info(f'Stopping PiAware Bluetooth LE services for piaware configuration')

    stop_systemd_service('piaware-wifi-scan.service')
    stop_systemd_service('piaware-ble-connect.service')

def start_piaware_configurator():
    logger.debug(f'Starting piaware-configurator...')
    start_systemd_service('piaware-configurator.service')

def restart_piaware_configurator():
    logger.debug(f'Restarting piaware-configurator...')
    restart_systemd_service('piaware-configurator.service')

def start_piaware_wifi_scan():
    logger.debug(f'Starting piaware-wifi-scan...')
    start_systemd_service('piaware-wifi-scan.service')

